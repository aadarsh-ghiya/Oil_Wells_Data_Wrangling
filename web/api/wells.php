<?php
declare(strict_types=1);

header("Content-Type: application/json; charset=utf-8");

function send_json(array $payload, int $status = 200): void
{
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

$config_path = __DIR__ . "/config.php";
if (!file_exists($config_path)) {
    send_json(
        ["error" => "Missing config.php. Copy web/api/config.php.example to web/api/config.php and set credentials."],
        500
    );
}

require $config_path;

$required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS", "DB_TABLE"];
foreach ($required as $variable) {
    if (!isset(${$variable}) || ${$variable} === "") {
        send_json(["error" => "Missing required database setting: {$variable}"], 500);
    }
}

if (!preg_match("/^[A-Za-z0-9_]+$/", $DB_TABLE)) {
    send_json(["error" => "DB_TABLE can only contain letters, numbers, and underscores."], 500);
}

$dsn = "mysql:host={$DB_HOST};port={$DB_PORT};dbname={$DB_NAME};charset=utf8mb4";

try {
    $pdo = new PDO(
        $dsn,
        $DB_USER,
        $DB_PASS,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );

    $statement = $pdo->query("SELECT * FROM `{$DB_TABLE}`");
    $rows = $statement->fetchAll();

    send_json([
        "count" => count($rows),
        "wells" => $rows
    ]);
} catch (Throwable $error) {
    send_json(["error" => "Database query failed: " . $error->getMessage()], 500);
}
