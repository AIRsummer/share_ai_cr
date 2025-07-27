<?php
// 测试各种错误检测

class badExample {  // 类名问题
    public $data;   // public属性问题
    
    // 死循环示例1
    function infiniteLoop1() {
        while (true) {
            echo "This will run forever";
            // 没有break语句
        }
    }
    
    // 死循环示例2 - for循环
    function infiniteLoop2() {
        for ($i = 0; $i < 10; ) {  // 缺少$i++
            echo $i;
        }
    }
    
    // 无限递归
    function recursiveFunction($n) {
        return $this->recursiveFunction($n);  // 没有终止条件
    }
    
    // SQL注入风险
    function sqlInjection($userId) {
        $query = "SELECT * FROM users WHERE id = $userId";  // 直接拼接
        $result = mysql_query($query);  // 没有错误处理
        return $result;
    }
    
    // XSS风险
    function xssRisk() {
        $name = $_GET['name'];  // 直接使用用户输入
        echo "Hello " . $name;  // 没有过滤
    }
    
    // 密码安全问题
    function passwordIssue($password) {
        $hashedPassword = $password;  // 明文存储
        return $hashedPassword;
    }
    
    // 硬编码凭据
    function hardcodedCredentials() {
        $pdo = new PDO('mysql:host=localhost;dbname=test', 'root', '123456');
        return $pdo;
    }
    
    // 循环内数据库查询 (N+1问题)
    function queryInLoop($userIds) {
        foreach ($userIds as $id) {
            $query = "SELECT * FROM users WHERE id = $id";
            $result = mysql_query($query);  // 每次循环都查询数据库
        }
    }
    
    // 内存泄漏风险
    function memoryLeak() {
        while (true) {
            $bigObject = new LargeObject();  // 循环内创建大对象
            $bigObject->loadHugeData();
            // 没有unset($bigObject)
            break;  // 这里有break，但演示内存问题
        }
    }
    
    // 除零错误
    function divisionByZero($a, $b) {
        return $a / $b;  // 没有检查$b是否为0
    }
    
    // 数组越界
    function arrayBounds($arr, $index) {
        return $arr[$index];  // 没有检查$index是否存在
    }
    
    // 文件操作缺少检查
    function fileOperation($filename) {
        $content = file_get_contents($filename);  // 没有检查文件是否存在
        return $content;
    }
    
    // 空的catch块
    function emptyCatch() {
        try {
            $result = riskyOperation();
        } catch (Exception $e) {
            // 空的catch块 - 忽略所有异常
        }
    }
    
    // 循环内字符串连接
    function stringConcatInLoop($items) {
        $result = "";
        for ($i = 0; $i < count($items); $i++) {  // count()在循环条件中
            $result .= $items[$i];  // 字符串连接在循环中
        }
        return $result;
    }
    
    // 循环内正则表达式
    function regexInLoop($texts) {
        foreach ($texts as $text) {
            if (preg_match('/pattern/', $text)) {  // 每次都编译正则
                echo $text;
            }
        }
    }
}

// 全局变量
$globalUser = null;

// 直接执行代码
if ($_POST['action'] == 'delete') {  // XSS风险
    $controller = new badExample();
    $controller->deleteUser($_POST['user_id']);  // 方法不存在
}

// 更多死循环示例
while (1) {
    echo "Another infinite loop";
}
?>