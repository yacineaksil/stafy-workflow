<?php
/** @var array $email */
$border = priority_border((int)($email['priority'] ?? 3));
$date   = substr($email['date'] ?? '', 0, 10);
?>
<a href="email.php?id=<?= urlencode($email['id']) ?>"
   class="block bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all <?= $border ?>">
    <div class="p-5">
        <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
                <div class="flex flex-wrap items-center gap-2 mb-1.5">
                    <?= category_badge($email['category'] ?? 'normal') ?>
                    <?php if (!empty($email['action_required'])): ?>
                        <span class="bg-yellow-50 text-yellow-700 border border-yellow-200 text-xs font-semibold px-2.5 py-0.5 rounded-full">ACTION REQUISE</span>
                    <?php endif; ?>
                    <?php if (!empty($email['deadline'])): ?>
                        <span class="bg-pink-50 text-pink-700 border border-pink-200 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                            ⏰ <?= htmlspecialchars($email['deadline']) ?>
                        </span>
                    <?php endif; ?>
                </div>
                <h3 class="font-semibold text-gray-900 truncate"><?= htmlspecialchars($email['subject'] ?? '(Sans objet)') ?></h3>
                <p class="text-sm text-gray-500 mt-0.5">De : <span class="font-medium text-gray-700"><?= htmlspecialchars($email['sender'] ?? '') ?></span></p>
                <?php if (!empty($email['summary'])): ?>
                    <p class="text-sm text-gray-600 mt-2 line-clamp-2"><?= htmlspecialchars($email['summary']) ?></p>
                <?php endif; ?>
                <?php if (!empty($email['action_description'])): ?>
                    <p class="text-xs text-amber-700 bg-amber-50 rounded-md px-3 py-1.5 mt-2 font-medium">
                        → <?= htmlspecialchars($email['action_description']) ?>
                    </p>
                <?php endif; ?>
            </div>
            <div class="flex flex-col items-end gap-2 flex-shrink-0">
                <p class="text-xs text-gray-400"><?= htmlspecialchars($date) ?></p>
                <?php $p = (int)($email['priority'] ?? 0); if ($p > 0): ?>
                    <div class="flex items-center gap-1">
                        <?php for ($i = 0; $i < 5; $i++): ?>
                            <div class="w-1.5 h-1.5 rounded-full <?= $i < $p ? priority_bar_color($p) : 'bg-gray-200' ?>"></div>
                        <?php endfor; ?>
                    </div>
                <?php endif; ?>
                <?php if (!empty($email['draft_reply'])): ?>
                    <span class="text-xs text-green-600 font-medium flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                        </svg>
                        Réponse suggérée
                    </span>
                <?php endif; ?>
            </div>
        </div>
    </div>
</a>
