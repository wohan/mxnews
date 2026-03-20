<?php
/**
 * MX NEWS - Simple Visitor Counter
 * Saves visit statistics to JSON file
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');

// Configuration
$STATS_FILE = __DIR__ . '/visitor_stats.json';
$IP_FILE = __DIR__ . '/daily_ips.json';

// Create directory if needed
if (!file_exists(__DIR__)) {
    mkdir(__DIR__, 0755, true);
}

// Initialize stats file
if (!file_exists($STATS_FILE)) {
    $initial_stats = [
        'total_visits' => 0,
        'unique_visitors' => 0,
        'daily_stats' => [],
        'last_updated' => date('Y-m-d H:i:s')
    ];
    file_put_contents($STATS_FILE, json_encode($initial_stats, JSON_PRETTY_PRINT));
}

// Initialize IP file
if (!file_exists($IP_FILE)) {
    file_put_contents($IP_FILE, json_encode([], JSON_PRETTY_PRINT));
}

// Get client info
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
$referer = $_SERVER['HTTP_REFERER'] ?? 'direct';
$date = date('Y-m-d');
$time = date('H:i:s');

// Load stats
$stats = json_decode(file_get_contents($STATS_FILE), true);
$daily_ips = json_decode(file_get_contents($IP_FILE), true);

// Check if this IP already visited today
$is_unique = true;
if (isset($daily_ips[$date])) {
    if (in_array($ip, $daily_ips[$date])) {
        $is_unique = false;
    } else {
        $daily_ips[$date][] = $ip;
    }
} else {
    $daily_ips[$date] = [$ip];
}

// Update stats
$stats['total_visits']++;
if ($is_unique) {
    $stats['unique_visitors']++;
}

// Update daily stats
if (!isset($stats['daily_stats'][$date])) {
    $stats['daily_stats'][$date] = [
        'visits' => 0,
        'unique' => 0
    ];
}
$stats['daily_stats'][$date]['visits']++;
if ($is_unique) {
    $stats['daily_stats'][$date]['unique']++;
}

$stats['last_updated'] = date('Y-m-d H:i:s');

// Save updated stats
file_put_contents($STATS_FILE, json_encode($stats, JSON_PRETTY_PRINT));
file_put_contents($IP_FILE, json_encode($daily_ips, JSON_PRETTY_PRINT));

// Prepare response
$response = [
    'success' => true,
    'stats' => [
        'total_visits' => $stats['total_visits'],
        'unique_visitors' => $stats['unique_visitors'],
        'today_visits' => $stats['daily_stats'][$date]['visits'],
        'today_unique' => $stats['daily_stats'][$date]['unique'],
        'is_unique_today' => $is_unique,
        'date' => $date,
        'time' => $time
    ],
    'message' => $is_unique ? 'Новое посещение сегодня!' : 'Добро пожаловать обратно!'
];

echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
?>