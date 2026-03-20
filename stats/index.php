<?php
/**
 * MX NEWS - Statistics Dashboard
 * Shows visitor statistics
 */

$STATS_FILE = __DIR__ . '/visitor_stats.json';

if (!file_exists($STATS_FILE)) {
    die('Статистика ещё не собрана. Посетите главную страницу для начала сбора данных.');
}

$stats = json_decode(file_get_contents($STATS_FILE), true);

// Calculate some metrics
$today = date('Y-m-d');
$today_visits = $stats['daily_stats'][$today]['visits'] ?? 0;
$today_unique = $stats['daily_stats'][$today]['unique'] ?? 0;

// Get last 7 days
$last_7_days = [];
for ($i = 6; $i >= 0; $i--) {
    $date = date('Y-m-d', strtotime("-$i days"));
    $last_7_days[$date] = $stats['daily_stats'][$date] ?? ['visits' => 0, 'unique' => 0];
}

// Calculate averages
$total_days = count($stats['daily_stats']);
$avg_daily_visits = $total_days > 0 ? round($stats['total_visits'] / $total_days, 1) : 0;
$avg_daily_unique = $total_days > 0 ? round($stats['unique_visitors'] / $total_days, 1) : 0;
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MX NEWS - Статистика посещений</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px 0; margin-bottom: 30px; border-radius: 10px; }
        h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .subtitle { font-size: 1.2rem; opacity: 0.9; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #1a237e; margin-bottom: 15px; font-size: 1.2rem; }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: #283593; }
        .stat-label { color: #666; font-size: 0.9rem; margin-top: 5px; }
        .table-container { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #1a237e; color: white; padding: 15px; text-align: left; }
        td { padding: 12px 15px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f9f9f9; }
        .badge { display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        .badge-success { background: #4caf50; color: white; }
        .badge-info { background: #2196f3; color: white; }
        .footer { text-align: center; margin-top: 40px; color: #666; font-size: 0.9rem; }
        .last-updated { background: #e8eaf6; padding: 10px; border-radius: 5px; margin-top: 20px; }
        .chart-container { height: 300px; margin-top: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { color: #1a237e; text-decoration: none; margin-right: 15px; }
        .nav a:hover { text-decoration: underline; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 MX NEWS - Статистика посещений</h1>
            <p class="subtitle">Аналитика трафика сайта новостей мотокросса</p>
        </header>
        
        <div class="nav">
            <a href="/">← На главную</a>
            <a href="/stats/counter.php?json=1" target="_blank">JSON данные</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Всего посещений</h3>
                <div class="stat-value"><?php echo number_format($stats['total_visits']); ?></div>
                <div class="stat-label">С начала отслеживания</div>
            </div>
            
            <div class="stat-card">
                <h3>Уникальных посетителей</h3>
                <div class="stat-value"><?php echo number_format($stats['unique_visitors']); ?></div>
                <div class="stat-label">Разные IP-адреса</div>
            </div>
            
            <div class="stat-card">
                <h3>Посещений сегодня</h3>
                <div class="stat-value"><?php echo number_format($today_visits); ?></div>
                <div class="stat-label"><?php echo $today_unique; ?> уникальных</div>
            </div>
            
            <div class="stat-card">
                <h3>Среднее в день</h3>
                <div class="stat-value"><?php echo $avg_daily_visits; ?></div>
                <div class="stat-label"><?php echo $avg_daily_unique; ?> уникальных</div>
            </div>
        </div>
        
        <div class="table-container">
            <h3>📈 Посещения за последние 7 дней</h3>
            <div class="chart-container">
                <canvas id="visitsChart"></canvas>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Дата</th>
                        <th>Всего посещений</th>
                        <th>Уникальных</th>
                        <th>Конверсия</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($last_7_days as $date => $day_stats): 
                        $conversion = $day_stats['visits'] > 0 ? round(($day_stats['unique'] / $day_stats['visits']) * 100, 1) : 0;
                    ?>
                    <tr>
                        <td><strong><?php echo date('d.m.Y', strtotime($date)); ?></strong></td>
                        <td><?php echo number_format($day_stats['visits']); ?></td>
                        <td><?php echo number_format($day_stats['unique']); ?></td>
                        <td>
                            <span class="badge <?php echo $conversion > 50 ? 'badge-success' : 'badge-info'; ?>">
                                <?php echo $conversion; ?>%
                            </span>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        
        <div class="last-updated">
            <p><strong>Последнее обновление:</strong> <?php echo $stats['last_updated']; ?></p>
            <p><strong>Дней отслеживания:</strong> <?php echo $total_days; ?></p>
            <p><strong>Файл статистики:</strong> <?php echo basename($STATS_FILE); ?> (<?php echo round(filesize($STATS_FILE) / 1024, 2); ?> KB)</p>
        </div>
        
        <div class="footer">
            <p>MX NEWS Statistics &copy; 2026 | Данные обновляются в реальном времени</p>
            <p>Статистика собирается анонимно, без сохранения персональных данных</p>
        </div>
    </div>
    
    <script>
        // Prepare chart data
        const dates = <?php echo json_encode(array_keys($last_7_days)); ?>;
        const visits = <?php echo json_encode(array_column($last_7_days, 'visits')); ?>;
        const unique = <?php echo json_encode(array_column($last_7_days, 'unique')); ?>;
        
        // Format dates for display
        const formattedDates = dates.map(date => {
            const d = new Date(date);
            return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
        });
        
        // Create chart
        const ctx = document.getElementById('visitsChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: formattedDates,
                datasets: [
                    {
                        label: 'Всего посещений',
                        data: visits,
                        borderColor: '#1a237e',
                        backgroundColor: 'rgba(26, 35, 126, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Уникальных посетителей',
                        data: unique,
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Динамика посещений за неделю'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Количество посещений'
                        }
                    }
                }
            }
        });
        
        // Auto-refresh every 5 minutes
        setTimeout(() => {
            location.reload();
        }, 5 * 60 * 1000);
    </script>
</body>
</html>