<?php
// 缺少命名空间和类注释

class userController {  // 类名应该是 UserController (大写)
    private $db;
    public $users;  // 不应该是 public

    // 构造函数缺少参数类型声明
    function __construct($database) {
        $this->db = $database;
    }

    // 方法名不规范，参数缺少类型声明
    public function getUserById($userId, $includeProfile = null) {
        // 直接使用 $_GET，存在安全风险
        $extra = $_GET['extra'];
        
        // SQL注入风险
        $query = "SELECT * FROM users WHERE id = $userId";
        
        // 没有错误处理
        $result = $this->db->query($query);
        
        // 直接返回数据库结果，没有数据验证
        return $result;
    }

    // 方法太长，职责不单一
    public function processUserData($data) {
        // 没有输入验证
        $name = $data['name'];
        $email = $data['email'];
        $password = $data['password'];
        
        // 密码明文存储
        $hashedPassword = $password;
        
        // 硬编码的数据库连接
        $pdo = new PDO('mysql:host=localhost;dbname=test', 'root', '123456');
        
        // 没有预处理语句
        $sql = "INSERT INTO users (name, email, password) VALUES ('$name', '$email', '$hashedPassword')";
        $pdo->exec($sql);
        
        // 发送邮件逻辑混在一起
        mail($email, "Welcome", "Welcome to our site");
        
        // 没有返回值
    }

    // 缺少访问修饰符
    function deleteUser($id) {
        // 没有权限检查
        // 没有软删除，直接硬删除
        $sql = "DELETE FROM users WHERE id = " . $id;
        $this->db->query($sql);
        
        // 没有返回操作结果
    }
}

// 全局变量
$globalUser = null;

// 直接执行代码，没有适当的入口点
if ($_POST['action'] == 'delete') {
    $controller = new userController($db);
    $controller->deleteUser($_POST['user_id']);
}
?>