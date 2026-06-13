<!DOCTYPE html>
<html lang="fr" class="h-full">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title><?= $page_title ?? 'Stafy – Assistante Exécutive' ?></title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: { stafy: { 50:'#f0f7ff',100:'#e0effe',600:'#1d6fc4',700:'#1558a0',900:'#0d3a6e' } } } }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', system-ui, sans-serif; }
    </style>
</head>
<body class="bg-gray-50 min-h-full">

<!-- Navbar -->
<nav class="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 bg-stafy-700 rounded-lg flex items-center justify-center">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                </div>
                <div>
                    <a href="index.php" class="font-bold text-gray-900 text-lg tracking-tight">Stafy</a>
                    <span class="text-gray-400 text-sm ml-1">Assistante Exécutive</span>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="index.php" class="text-sm text-gray-600 hover:text-gray-900 font-medium px-3 py-1.5 rounded-md hover:bg-gray-100 transition">
                    Dashboard
                </a>
                <a href="refresh.php"
                   class="inline-flex items-center gap-2 bg-stafy-700 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-stafy-900 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    Actualiser
                </a>
            </div>
        </div>
    </div>
</nav>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
