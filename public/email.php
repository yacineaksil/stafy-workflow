<?php
require_once __DIR__ . '/config.php';

$id  = $_GET['id'] ?? '';
$pdo = get_db();

if (!$pdo || !$id) {
    header('Location: index.php');
    exit;
}

$email = $pdo->prepare("
    SELECT e.*, a.category, a.priority, a.sentiment, a.summary, a.key_points,
           a.action_required, a.action_description, a.deadline, a.draft_reply, a.analyzed_at
    FROM emails e
    LEFT JOIN email_analyses a ON e.id = a.email_id
    WHERE e.id = ?
");
$email->execute([$id]);
$email = $email->fetch();

if (!$email) {
    header('Location: index.php');
    exit;
}

$key_points = json_decode_safe($email['key_points'] ?? '');
$p          = (int)($email['priority'] ?? 3);

$page_title = htmlspecialchars($email['subject'] ?? 'Email') . ' – Stafy';
require_once __DIR__ . '/includes/header.php';
?>

<!-- Retour -->
<div class="mb-6">
    <a href="index.php" class="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        Retour au dashboard
    </a>
</div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

    <!-- Email -->
    <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-7 <?= priority_border($p) ?>">
            <div class="flex flex-wrap items-center gap-2 mb-4">
                <?= category_badge($email['category'] ?? 'normal') ?>
                <?php if (!empty($email['action_required'])): ?>
                    <span class="bg-yellow-50 text-yellow-700 border border-yellow-200 text-xs font-semibold px-3 py-1 rounded-full">ACTION REQUISE</span>
                <?php endif; ?>
                <?php if (!empty($email['sentiment'])): ?>
                    <span class="bg-gray-50 text-gray-600 border border-gray-200 text-xs font-medium px-3 py-1 rounded-full">
                        <?= htmlspecialchars($email['sentiment']) ?>
                    </span>
                <?php endif; ?>
            </div>

            <h1 class="text-xl font-bold text-gray-900 mb-5"><?= htmlspecialchars($email['subject'] ?? '(Sans objet)') ?></h1>

            <div class="grid grid-cols-2 gap-3 text-sm mb-6">
                <div>
                    <p class="text-gray-400 text-xs uppercase tracking-wide font-semibold mb-0.5">De</p>
                    <p class="text-gray-800 font-medium"><?= htmlspecialchars($email['sender'] ?? '') ?></p>
                    <p class="text-gray-500 text-xs"><?= htmlspecialchars($email['sender_email'] ?? '') ?></p>
                </div>
                <div>
                    <p class="text-gray-400 text-xs uppercase tracking-wide font-semibold mb-0.5">Reçu le</p>
                    <p class="text-gray-800"><?= htmlspecialchars(substr($email['date'] ?? '', 0, 16)) ?></p>
                </div>
                <?php if (!empty($email['deadline'])): ?>
                    <div class="col-span-2">
                        <p class="text-gray-400 text-xs uppercase tracking-wide font-semibold mb-0.5">Échéance</p>
                        <p class="text-red-700 font-medium">⏰ <?= htmlspecialchars($email['deadline']) ?></p>
                    </div>
                <?php endif; ?>
            </div>

            <div class="border-t border-gray-100 pt-5">
                <p class="text-gray-700 leading-relaxed whitespace-pre-wrap text-sm"><?= htmlspecialchars($email['body'] ?? $email['snippet'] ?? '') ?></p>
            </div>
        </div>
    </div>

    <!-- Panneau latéral -->
    <div class="space-y-5">

        <!-- Analyse Stafy -->
        <?php if (!empty($email['summary'])): ?>
        <div class="bg-gradient-to-br from-stafy-900 to-stafy-700 text-white rounded-2xl p-6 shadow-lg">
            <p class="text-xs font-semibold text-white/60 uppercase tracking-widest mb-2">Analyse Stafy</p>
            <p class="text-white font-medium text-sm leading-relaxed"><?= htmlspecialchars($email['summary']) ?></p>

            <?php if (!empty($key_points)): ?>
            <div class="mt-4 pt-4 border-t border-white/20">
                <p class="text-xs font-semibold text-white/60 uppercase tracking-widest mb-2">Points clés</p>
                <ul class="space-y-1.5">
                    <?php foreach ($key_points as $point): ?>
                        <li class="flex items-start gap-2 text-sm text-white/85">
                            <span class="text-white/50 flex-shrink-0 mt-0.5">•</span>
                            <?= htmlspecialchars($point) ?>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>
        </div>
        <?php endif; ?>

        <!-- Action requise -->
        <?php if (!empty($email['action_description'])): ?>
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-5">
            <p class="text-xs font-semibold text-amber-600 uppercase tracking-widest mb-2">Action requise</p>
            <p class="text-amber-800 text-sm font-medium"><?= htmlspecialchars($email['action_description']) ?></p>
        </div>
        <?php endif; ?>

        <!-- Brouillon de réponse -->
        <?php if (!empty($email['draft_reply'])): ?>
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div class="flex items-center justify-between mb-3">
                <p class="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                    </svg>
                    Réponse suggérée
                </p>
                <button onclick="copyDraft()" class="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors">Copier</button>
            </div>
            <div id="draft-content" class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap border border-gray-100"><?= htmlspecialchars($email['draft_reply']) ?></div>
        </div>
        <?php endif; ?>

        <!-- Priorité -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">Priorité</p>
            <div class="flex items-center gap-2">
                <?php for ($i = 0; $i < 5; $i++): ?>
                    <div class="flex-1 h-2.5 rounded-full <?= $i < $p ? priority_bar_color($p) : 'bg-gray-100' ?>"></div>
                <?php endfor; ?>
            </div>
            <p class="text-xs text-gray-500 mt-2"><?= priority_label($p) ?></p>
        </div>

    </div>
</div>

<script>
function copyDraft() {
    navigator.clipboard.writeText(document.getElementById('draft-content').innerText).then(() => {
        event.target.textContent = 'Copié !';
        setTimeout(() => event.target.textContent = 'Copier', 2000);
    });
}
</script>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
