<?php
// demo_code/BadCode.php - 故意写的有问题的代码
class OrderProcessor
{
    public function processOrder($orderId, $userId, $items, $discount, $shippingAddress, $billingAddress, $paymentMethod, $specialInstructions) 
    {
        // 长参数列表异味
        
        if ($orderId < 1) {
            throw new Exception("Invalid order");
        }
        
        $total = 0;
        foreach ($items as $item) {
            if ($item['price'] > 0) {
                if ($item['quantity'] > 0) {
                    if ($item['category'] == 'electronics') {
                        if ($item['warranty'] == true) {
                            $total += $item['price'] * $item['quantity'] * 1.1; // 深层嵌套
                        } else {
                            $total += $item['price'] * $item['quantity'];
                        }
                    } else {
                        $total += $item['price'] * $item['quantity'];
                    }
                }
            }
        }
        
        // 重复的折扣计算逻辑（业务不一致）
        if ($userId == 'VIP') {
            $total = $total * 0.8; // 20%折扣
        }
        
        // 硬编码的配置数据
        $shippingCost = 15.99;
        $taxRate = 0.085;
        
        $finalTotal = $total + $shippingCost + ($total * $taxRate);
        
        // SQL注入风险
        $sql = "INSERT INTO orders (user_id, total) VALUES (" . $userId . ", " . $finalTotal . ")";
        
        // 执行订单处理...
        $this->processPayment($paymentMethod, $finalTotal);
        $this->sendNotification($userId);
        $this->updateInventory($items);
        $this->logOrder($orderId);
        
        return $finalTotal;
    }
    
    // 重复的VIP折扣逻辑，但比例不同
    public function calculateVipDiscount($amount, $userType) 
    {
        if ($userType == 'VIP') {
            return $amount * 0.85; // 15%折扣 - 与上面不一致！
        }
        return $amount;
    }
    
    // 其他方法...
    public function processPayment($method, $amount) { /* ... */ }
    public function sendNotification($userId) { /* ... */ }
    public function updateInventory($items) { /* ... */ }
    public function logOrder($orderId) { /* ... */ }
}