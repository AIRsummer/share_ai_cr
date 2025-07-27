class userService {  // 应该是 UserService
    public function getUser($id){  // 缺少空格
        if($id<1)return null;  // 格式不规范


        // 模拟死循环
        $k = 100;
        while($k > 0) {
            echo $k;
            /*** do something ***/
        }
    }


    public function getUser($id) {
    $sql = "SELECT * FROM users WHERE id = " . $id; // SQL注入风险
    return $this->db->query($sql);
}
}