<?php
require_once __DIR__ . '/config.php';

$pdo   = get_db();
$error = null;

// Stats
$stats = ['total_unread' => 0, 'urgent' => 0, 'important' => 0, 'with_drafts' => 0, 'processed_today' => 0];

// Emails avec analyses
$emails = [];

// Briefing du jour
$briefing = null;

// Dernier refresh
$last_refresh = null;
$log_file     = LOGS_DIR . '/cron.log';

if ($pdo) {
    try {
        $today = date('Y-m-d');

        $row = $pdo->query("
            SELECT
                COUNT(CASE WHEN e.is_read = 0 THEN 1 END)                    AS total_unread,
                COUNT(CASE WHEN a.category = 'urgent' THEN 1 END)            AS urgent,
                COUNT(CASE WHEN a.category = 'important' THEN 1 END)         AS important,
                COUNT(CASE WHEN a.draft_reply IS NOT NULL THEN 1 END)         AS with_drafts,
                COUNT(CASE WHEN date(e.fetched_at) = '$today' THEN 1 END)    AS processed_today
            FROM emails e
            LEFT JOIN email_analyses a ON e.id = a.email_id
        ")->fetch();
        if ($row) $stats = $row;

        $stmt = $pdo->query("
            SELECT e.id, e.subject, e.sender, e.sender_email, e.date, e.snippet, e.is_read,
                   a.category, a.priority, a.sentiment, a.summary, a.key_points,
                   a.action_required, a.action_description, a.deadline, a.draft_reply
            FROM emails e
            LEFT JOIN email_analyses a ON e.id = a.email_id
            ORDER BY COALESCE(a.priority, 0) DESC, e.date DESC
            LIMIT 100
        ");
        $emails = $stmt->fetchAll();

        $b = $pdo->query("SELECT * FROM daily_briefings ORDER BY created_at DESC LIMIT 1")->fetch();
        if ($b) {
            $briefing = $b;
            $briefing['priority_list'] = json_decode_safe($b['priority_list']);
            $briefing['alerts']        = json_decode_safe($b['alerts']);
        }
    } catch (Exception $e) {
        $error = 'Erreur base de données : ' . $e->getMessage();
    }
} else {
    $error = 'Base de données introuvable. Lancez <code>python cron_refresh.py</code> ou <code>python main.py demo</code> pour initialiser.';
}

// Segmentation par catégorie
$urgent_emails    = array_filter($emails, fn($e) => ($e['category'] ?? '') === 'urgent');
$important_emails = array_filter($emails, fn($e) => ($e['category'] ?? '') === 'important');
$other_emails     = array_filter($emails, fn($e) => !in_array($e['category'] ?? '', ['urgent', 'important']));

// Statut refresh flag
$refresh_pending = file_exists(REFRESH_FLAG);

// Log du dernier cron
if (file_exists($log_file)) {
    $last_refresh = date('d/m/Y H:i', filemtime($log_file));
}

$page_title = 'Dashboard – Stafy';
require_once __DIR__ . '/includes/header.php';
?>

<!-- Titre + statut -->
<div class="mb-6 flex items-center justify-between">
    <div>
        <h1 class="text-2xl font-bold text-gray-900">Tableau de Bord</h1>
        <p class="text-gray-500 text-sm mt-0.5"><?= date('l d F Y') ?> – <?= date('H:i') ?>
            <?php if ($last_refresh): ?>
                · Dernier refresh : <span class="text-blue-600"><?= $last_refresh ?></span>
            <?php endif; ?>
        </p>
    </div>
    <?php if ($refresh_pending): ?>
        <div class="flex items-center gap-2 text-sm text-blue-700 bg-blue-50 border border-blue-200 px-4 py-2 rounded-lg">
            <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Refresh demandé – en attente du cron…
        </div>
    <?php endif; ?>
</div>

<?php if ($_GET['refreshed'] ?? false): ?>
    <div class="mb-4 bg-green-50 border border-green-200 text-green-800 text-sm px-4 py-3 rounded-xl">
        ✓ Demande de refresh envoyée. Le prochain passage du cron analysera vos emails.
    </div>
<?php endif; ?>

<?php if ($error): ?>
    <div class="mb-6 bg-red-50 border border-red-200 text-red-800 text-sm px-5 py-4 rounded-xl">
        <?= $error ?>
    </div>
<?php endif; ?>

<!-- KPI -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Non lus</p>
        <p class="text-3xl font-bold text-gray-900 mt-1"><?= $stats['total_unread'] ?></p>
        <p class="text-xs text-gray-400 mt-1">emails en attente</p>
    </div>
    <div class="bg-red-50 rounded-xl shadow-sm border border-red-100 p-5">
        <p class="text-xs font-semibold text-red-400 uppercase tracking-wide">Urgents</p>
        <p class="text-3xl font-bold text-red-600 mt-1"><?= $stats['urgent'] ?></p>
        <p class="text-xs text-red-400 mt-1">réponse &lt; 2h</p>
    </div>
    <div class="bg-orange-50 rounded-xl shadow-sm border border-orange-100 p-5">
        <p class="text-xs font-semibold text-orange-400 uppercase tracking-wide">Importants</p>
        <p class="text-3xl font-bold text-orange-600 mt-1"><?= $stats['important'] ?></p>
        <p class="text-xs text-orange-400 mt-1">à traiter aujourd'hui</p>
    </div>
    <div class="bg-blue-50 rounded-xl shadow-sm border border-blue-100 p-5">
        <p class="text-xs font-semibold text-blue-400 uppercase tracking-wide">Brouillons</p>
        <p class="text-3xl font-bold text-blue-600 mt-1"><?= $stats['with_drafts'] ?></p>
        <p class="text-xs text-blue-400 mt-1">réponses suggérées</p>
    </div>
</div>

<!-- Briefing exécutif -->
<?php if ($briefing): ?>
<div class="bg-gradient-to-r from-stafy-900 to-stafy-700 text-white rounded-2xl p-7 mb-8 shadow-lg">
    <div class="flex items-start gap-4">
        <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
        </div>
        <div class="flex-1">
            <p class="text-xs font-semibold text-white/60 uppercase tracking-widest mb-2">Briefing du Jour</p>
            <p class="text-white font-medium leading-relaxed"><?= htmlspecialchars($briefing['executive_summary'] ?? '') ?></p>

            <?php if (!empty($briefing['alerts'])): ?>
                <div class="mt-4 space-y-1.5">
                    <?php foreach ($briefing['alerts'] as $alert): ?>
                        <div class="flex items-start gap-2 text-sm text-amber-200">
                            <svg class="w-4 h-4 text-amber-300 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                            <?= htmlspecialchars($alert) ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>

    <?php if (!empty($briefing['priority_list'])): ?>
        <div class="mt-6 pt-6 border-t border-white/20">
            <p class="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3">Actions Prioritaires</p>
            <ol class="space-y-2">
                <?php foreach ($briefing['priority_list'] as $i => $action): ?>
                    <li class="flex items-start gap-3 text-sm text-white/90">
                        <span class="w-5 h-5 bg-white/20 rounded-full text-xs flex items-center justify-center flex-shrink-0 font-bold mt-0.5"><?= $i + 1 ?></span>
                        <?= htmlspecialchars($action) ?>
                    </li>
                <?php endforeach; ?>
            </ol>
        </div>
    <?php endif; ?>
</div>
<?php else: ?>
<div class="bg-gray-100 border border-dashed border-gray-300 rounded-2xl p-10 mb-8 text-center">
    <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
    </svg>
    <p class="text-gray-500 font-medium">Aucun briefing disponible</p>
    <p class="text-gray-400 text-sm mt-1">Cliquez sur « Actualiser » pour lancer une analyse</p>
    <a href="refresh.php" class="inline-block mt-4 bg-stafy-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-stafy-900 transition-colors">
        Analyser mes emails
    </a>
</div>
<?php endif; ?>

<!-- Urgents -->
<?php if (!empty($urgent_emails)): ?>
<div class="mb-8">
    <h2 class="text-base font-bold text-red-700 mb-3 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
        URGENTS – Réponse immédiate requise (<?= count($urgent_emails) ?>)
    </h2>
    <div class="space-y-3">
        <?php foreach ($urgent_emails as $email): ?>
            <?php include __DIR__ . '/includes/email_card.php'; ?>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<!-- Importants -->
<?php if (!empty($important_emails)): ?>
<div class="mb-8">
    <h2 class="text-base font-bold text-orange-700 mb-3 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
        </svg>
        IMPORTANTS – À traiter aujourd'hui (<?= count($important_emails) ?>)
    </h2>
    <div class="space-y-3">
        <?php foreach ($important_emails as $email): ?>
            <?php include __DIR__ . '/includes/email_card.php'; ?>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<!-- Autres -->
<?php if (!empty($other_emails)): ?>
<div class="mb-8">
    <h2 class="text-base font-semibold text-gray-600 mb-3 flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
        </svg>
        AUTRES (<?= count($other_emails) ?>)
    </h2>
    <div class="space-y-2">
        <?php foreach ($other_emails as $email): ?>
            <?php include __DIR__ . '/includes/email_card.php'; ?>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<?php if (empty($emails) && !$error): ?>
<div class="text-center py-16">
    <svg class="w-16 h-16 text-gray-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
    <p class="text-gray-400 text-lg font-medium">Aucun email analysé</p>
    <p class="text-gray-300 text-sm mt-1">Lancez une analyse pour commencer</p>
    <a href="refresh.php" class="inline-block mt-4 bg-stafy-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-stafy-900 transition-colors">
        Analyser mes emails
    </a>
</div>
<?php endif; ?>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
