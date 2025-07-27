<?php

/**
 * 用户控制器 - 包含多种代码异味的示例
 */
class user_controller_with_bad_naming {
    private $DB_CONNECTION;
    private $cache_manager;
    private $email_service;
    private $logging_service;
    private $validation_service;
    private $notification_service;
    
    public function __construct($db, $cache, $email, $logger, $validator, $notifier) {
        $this->DB_CONNECTION = $db;
        $this->cache_manager = $cache;
        $this->email_service = $email;
        $this->logging_service = $logger;
        $this->validation_service = $validator;
        $this->notification_service = $notifier;
    }
    
    // 极其复杂的用户处理方法 - 长方法 + 高复杂度
    public function PROCESS_USER_REGISTRATION_WITH_VALIDATION_AND_NOTIFICATIONS($user_data, $validation_rules, $email_settings, $notification_settings, $logging_options, $cache_options, $security_settings) {
        $processed_users = [];
        $errors = [];
        
        if (is_array($user_data) && count($user_data) > 0) {
            foreach ($user_data as $index => $single_user) {
                if (isset($single_user['email']) && !empty($single_user['email'])) {
                    if (filter_var($single_user['email'], FILTER_VALIDATE_EMAIL)) {
                        if (isset($validation_rules['email_domain_check']) && $validation_rules['email_domain_check'] === true) {
                            $email_domain = substr(strrchr($single_user['email'], "@"), 1);
                            if (isset($validation_rules['allowed_domains']) && is_array($validation_rules['allowed_domains'])) {
                                if (in_array($email_domain, $validation_rules['allowed_domains'])) {
                                    if (isset($single_user['name']) && strlen(trim($single_user['name'])) > 2) {
                                        if (isset($validation_rules['name_validation']) && $validation_rules['name_validation'] === true) {
                                            if (preg_match('/^[a-zA-Z\s\-\'\.]+$/', $single_user['name'])) {
                                                if (isset($single_user['age']) && is_numeric($single_user['age'])) {
                                                    if ($single_user['age'] >= 18 && $single_user['age'] <= 120) {
                                                        if (isset($single_user['phone']) && !empty($single_user['phone'])) {
                                                            if (preg_match('/^[\+]?[1-9][\d]{0,15}$/', $single_user['phone'])) {
                                                                // 非常复杂的用户数据处理逻辑
                                                                $processed_user = [];
                                                                $processed_user['id'] = uniqid('user_', true);
                                                                $processed_user['email'] = strtolower(trim($single_user['email']));
                                                                $processed_user['name'] = ucwords(strtolower(trim($single_user['name'])));
                                                                $processed_user['age'] = intval($single_user['age']);
                                                                $processed_user['phone'] = preg_replace('/[^0-9+]/', '', $single_user['phone']);
                                                                $processed_user['registration_date'] = date('Y-m-d H:i:s');
                                                                $processed_user['status'] = 'pending';
                                                                
                                                                // 密码处理
                                                                if (isset($single_user['password']) && strlen($single_user['password']) >= 8) {
                                                                    if (isset($security_settings['password_encryption']) && $security_settings['password_encryption'] === true) {
                                                                        if (isset($security_settings['encryption_method'])) {
                                                                            switch ($security_settings['encryption_method']) {
                                                                                case 'bcrypt':
                                                                                    $processed_user['password'] = password_hash($single_user['password'], PASSWORD_BCRYPT);
                                                                                    break;
                                                                                case 'sha256':
                                                                                    $processed_user['password'] = hash('sha256', $single_user['password'] . $security_settings['salt']);
                                                                                    break;
                                                                                case 'md5':
                                                                                    $processed_user['password'] = md5($single_user['password']);
                                                                                    break;
                                                                                default:
                                                                                    $processed_user['password'] = $single_user['password'];
                                                                            }
                                                                        }
                                                                    } else {
                                                                        $processed_user['password'] = $single_user['password'];
                                                                    }
                                                                } else {
                                                                    $errors[] = "Password too short for user: " . $single_user['email'];
                                                                    continue;
                                                                }
                                                                
                                                                // 数据库存储逻辑
                                                                try {
                                                                    if (isset($cache_options['check_cache_first']) && $cache_options['check_cache_first'] === true) {
                                                                        $cache_key = 'user_email_' . md5($processed_user['email']);
                                                                        $cached_user = $this->cache_manager->get($cache_key);
                                                                        if ($cached_user !== null) {
                                                                            $errors[] = "User already exists in cache: " . $processed_user['email'];
                                                                            continue;
                                                                        }
                                                                    }
                                                                    
                                                                    $insert_sql = "INSERT INTO users (id, email, name, age, phone, password, registration_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
                                                                    $stmt = $this->DB_CONNECTION->prepare($insert_sql);
                                                                    $insert_result = $stmt->execute([
                                                                        $processed_user['id'],
                                                                        $processed_user['email'],
                                                                        $processed_user['name'],
                                                                        $processed_user['age'],
                                                                        $processed_user['phone'],
                                                                        $processed_user['password'],
                                                                        $processed_user['registration_date'],
                                                                        $processed_user['status']
                                                                    ]);
                                                                    
                                                                    if ($insert_result) {
                                                                        $processed_users[] = $processed_user;
                                                                        
                                                                        // 缓存处理
                                                                        if (isset($cache_options['cache_new_users']) && $cache_options['cache_new_users'] === true) {
                                                                            $cache_key = 'user_email_' . md5($processed_user['email']);
                                                                            $cache_ttl = isset($cache_options['ttl']) ? $cache_options['ttl'] : 3600;
                                                                            $this->cache_manager->set($cache_key, $processed_user, $cache_ttl);
                                                                        }
                                                                        
                                                                        // 邮件通知处理
                                                                        if (isset($email_settings['send_welcome_email']) && $email_settings['send_welcome_email'] === true) {
                                                                            if (isset($email_settings['template']) && is_array($email_settings['template'])) {
                                                                                $email_subject = str_replace('{name}', $processed_user['name'], $email_settings['template']['subject']);
                                                                                $email_body = str_replace(['{name}', '{email}'], [$processed_user['name'], $processed_user['email']], $email_settings['template']['body']);
                                                                                
                                                                                $email_result = $this->email_service->send(
                                                                                    $processed_user['email'],
                                                                                    $email_subject,
                                                                                    $email_body,
                                                                                    isset($email_settings['from']) ? $email_settings['from'] : 'noreply@example.com'
                                                                                );
                                                                                
                                                                                if (!$email_result) {
                                                                                    if (isset($logging_options['log_email_failures']) && $logging_options['log_email_failures'] === true) {
                                                                                        $this->logging_service->error("Failed to send welcome email to: " . $processed_user['email']);
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                        
                                                                        // 系统通知处理
                                                                        if (isset($notification_settings['send_admin_notification']) && $notification_settings['send_admin_notification'] === true) {
                                                                            $notification_message = "New user registered: " . $processed_user['name'] . " (" . $processed_user['email'] . ")";
                                                                            $this->notification_service->notify('admin', $notification_message);
                                                                        }
                                                                        
                                                                        // 日志记录
                                                                        if (isset($logging_options['log_successful_registrations']) && $logging_options['log_successful_registrations'] === true) {
                                                                            $this->logging_service->info("User successfully registered: " . $processed_user['email']);
                                                                        }
                                                                        
                                                                    } else {
                                                                        $errors[] = "Database insertion failed for user: " . $processed_user['email'];
                                                                        if (isset($logging_options['log_database_failures']) && $logging_options['log_database_failures'] === true) {
                                                                            $this->logging_service->error("Database insertion failed for user: " . $processed_user['email']);
                                                                        }
                                                                    }
                                                                    
                                                                } catch (Exception $e) {
                                                                    $errors[] = "Exception occurred while processing user: " . $single_user['email'] . " - " . $e->getMessage();
                                                                    if (isset($logging_options['log_exceptions']) && $logging_options['log_exceptions'] === true) {
                                                                        $this->logging_service->error("Exception in user registration: " . $e->getMessage());
                                                                    }
                                                                }
                                                                
                                                            } else {
                                                                $errors[] = "Invalid phone number format for user: " . $single_user['email'];
                                                            }
                                                        } else {
                                                            $errors[] = "Phone number is required for user: " . $single_user['email'];
                                                        }
                                                    } else {
                                                        $errors[] = "Invalid age for user: " . $single_user['email'];
                                                    }
                                                } else {
                                                    $errors[] = "Age is required and must be numeric for user: " . $single_user['email'];
                                                }
                                            } else {
                                                $errors[] = "Invalid name format for user: " . $single_user['email'];
                                            }
                                        } else {
                                            $errors[] = "Name validation is disabled, skipping user: " . $single_user['email'];
                                        }
                                    } else {
                                        $errors[] = "Name is too short for user: " . $single_user['email'];
                                    }
                                } else {
                                    $errors[] = "Email domain not allowed: " . $email_domain;
                                }
                            } else {
                                $errors[] = "Allowed domains configuration is missing or invalid";
                            }
                        } else {
                            $errors[] = "Email domain check is disabled, skipping user: " . $single_user['email'];
                        }
                    } else {
                        $errors[] = "Invalid email format: " . $single_user['email'];
                    }
                } else {
                    $errors[] = "Email is required for user at index: " . $index;
                }
            }
        } else {
            $errors[] = "User data is not a valid array or is empty";
        }
        
        return [
            'processed_users' => $processed_users,
            'errors' => $errors,
            'total_processed' => count($processed_users),
            'total_errors' => count($errors)
        ];
    }
    
    public function simple_get_user($id) {
        return $this->DB_CONNECTION->query("SELECT * FROM users WHERE id = " . $id);
    }
} 