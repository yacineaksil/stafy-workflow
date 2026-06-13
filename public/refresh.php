<?php
require_once __DIR__ . '/config.php';

// Crée le fichier flag – le cron job le détecte et lance un refresh immédiat
if (!file_exists(REFRESH_FLAG)) {
    file_put_contents(REFRESH_FLAG, date('Y-m-d H:i:s'));
}

header('Location: index.php?refreshed=1');
exit;
