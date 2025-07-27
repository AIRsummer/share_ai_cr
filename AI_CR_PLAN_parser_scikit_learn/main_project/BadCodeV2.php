<?php
class ErrorDemo {
    public function missingComma() {
        $x = 1
        $y = 2; // 缺少分号
        return $x + $y;
    }
    
    public function unclosedBrace() {
        if (true) {
            echo "test";
        // 缺少闭合括号
    
    public function invalidVariable() {
        $valid = "ok";
        invalid = "not ok"; // 缺少$符号
        return $valid;
    }
}
