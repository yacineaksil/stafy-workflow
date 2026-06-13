<?php
/**
 * Configuration Stafy – à adapter selon votre hébergement Hostinger.
 *
 * Sur Hostinger, le dépôt est typiquement dans /home/USERNAME/stafy-workflow/
 * Les fichiers PHP sont dans /home/USERNAME/public_html/stafy/ (ou sous-dossier).
 *
 * Remplacez YOUR_USERNAME par votre nom d'utilisateur Hostinger.
 */

define('DB_PATH',       '/home/YOUR_USERNAME/stafy-workflow/stafy.db');
define('REFRESH_FLAG',  '/home/YOUR_USERNAME/stafy-workflow/refresh.flag');
define('LOGS_DIR',      '/home/YOUR_USERNAME/stafy-workflow/logs');

// --- Helpers ---

function priority_label(int $p): string {
    return match($p) {
        5 => 'CRITIQUE', 4 => 'HAUTE', 3 => 'MOYENNE',
        2 => 'BASSE',    1 => 'NÉGLIGEABLE', default => '—',
    };
}

function priority_bar_color(int $p): string {
    return match($p) {
        5 => 'bg-red-500', 4 => 'bg-orange-500', 3 => 'bg-blue-500',
        2 => 'bg-green-500', default => 'bg-gray-300',
    };
}

function category_badge(string $cat): string {
    $classes = match($cat) {
        'urgent'     => 'bg-red-50 text-red-700 border border-red-200',
        'important'  => 'bg-orange-50 text-orange-700 border border-orange-200',
        'normal'     => 'bg-blue-50 text-blue-700 border border-blue-200',
        'newsletter' => 'bg-purple-50 text-purple-700 border border-purple-200',
        'spam'       => 'bg-gray-100 text-gray-500 border border-gray-200',
        default      => 'bg-gray-100 text-gray-500 border border-gray-200',
    };
    return '<span class="' . $classes . ' text-xs font-semibold px-2.5 py-0.5 rounded-full">'
         . strtoupper(htmlspecialchars($cat)) . '</span>';
}

function priority_border(int $p): string {
    return match($p) {
        5 => 'border-l-4 border-red-500',
        4 => 'border-l-4 border-orange-500',
        3 => 'border-l-4 border-blue-500',
        2 => 'border-l-4 border-green-500',
        default => 'border-l-4 border-gray-200',
    };
}

function get_db(): PDO {
    if (!file_exists(DB_PATH)) {
        return null;
    }
    $pdo = new PDO('sqlite:' . DB_PATH);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    return $pdo;
}

function json_decode_safe(string|null $val): array {
    if (!$val) return [];
    $decoded = json_decode($val, true);
    return is_array($decoded) ? $decoded : [];
}
