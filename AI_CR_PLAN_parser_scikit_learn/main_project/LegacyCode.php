<?php

// 遗留代码示例 - 包含多种代码异味

class data_processor_manager_service_handler {
    public $DATABASE_CONNECTION_OBJECT;
    public $file_system_manager;
    public $CACHE_STORAGE_SYSTEM;
    public $email_notification_sender;
    public $log_writer_component;
    
    function __construct($db, $fs, $cache, $emailer, $logger) {
        $this->DATABASE_CONNECTION_OBJECT = $db;
        $this->file_system_manager = $fs;
        $this->CACHE_STORAGE_SYSTEM = $cache;
        $this->email_notification_sender = $emailer;
        $this->log_writer_component = $logger;
    }
    
    function PROCESS_ALL_DATA_WITH_VALIDATION_CACHING_NOTIFICATION_AND_LOGGING($INPUT_DATA_ARRAY, $PROCESSING_OPTIONS_CONFIG, $VALIDATION_RULES_SET, $CACHE_CONFIGURATION_SETTINGS, $EMAIL_NOTIFICATION_PREFERENCES, $LOGGING_CONFIGURATION_OPTIONS, $FILE_STORAGE_SETTINGS, $DATABASE_OPERATION_OPTIONS, $ERROR_HANDLING_PREFERENCES) {
        $PROCESSED_RESULTS = array();
        $ERROR_MESSAGES_COLLECTION = array();
        $TOTAL_PROCESSING_TIME = 0;
        $MEMORY_USAGE_TRACKER = 0;
        
        if (isset($INPUT_DATA_ARRAY) && is_array($INPUT_DATA_ARRAY) && count($INPUT_DATA_ARRAY) > 0) {
            foreach ($INPUT_DATA_ARRAY as $CURRENT_INDEX => $CURRENT_DATA_ITEM) {
                $PROCESSING_START_TIME = microtime(true);
                $MEMORY_USAGE_BEFORE = memory_get_usage();
                
                if (isset($CURRENT_DATA_ITEM) && !empty($CURRENT_DATA_ITEM)) {
                    if (isset($VALIDATION_RULES_SET) && is_array($VALIDATION_RULES_SET) && count($VALIDATION_RULES_SET) > 0) {
                        $VALIDATION_PASSED = true;
                        
                        foreach ($VALIDATION_RULES_SET as $RULE_NAME => $RULE_CONFIGURATION) {
                            if (isset($RULE_CONFIGURATION['enabled']) && $RULE_CONFIGURATION['enabled'] === true) {
                                switch ($RULE_NAME) {
                                    case 'email_validation':
                                        if (isset($CURRENT_DATA_ITEM['email']) && !empty($CURRENT_DATA_ITEM['email'])) {
                                            if (!filter_var($CURRENT_DATA_ITEM['email'], FILTER_VALIDATE_EMAIL)) {
                                                $ERROR_MESSAGES_COLLECTION[] = "Invalid email format for item at index: " . $CURRENT_INDEX;
                                                $VALIDATION_PASSED = false;
                                            } else {
                                                if (isset($RULE_CONFIGURATION['domain_check']) && $RULE_CONFIGURATION['domain_check'] === true) {
                                                    $EMAIL_DOMAIN = substr(strrchr($CURRENT_DATA_ITEM['email'], "@"), 1);
                                                    if (isset($RULE_CONFIGURATION['allowed_domains']) && is_array($RULE_CONFIGURATION['allowed_domains'])) {
                                                        if (!in_array($EMAIL_DOMAIN, $RULE_CONFIGURATION['allowed_domains'])) {
                                                            $ERROR_MESSAGES_COLLECTION[] = "Email domain not allowed for item at index: " . $CURRENT_INDEX;
                                                            $VALIDATION_PASSED = false;
                                                        }
                                                    }
                                                }
                                            }
                                        } else {
                                            $ERROR_MESSAGES_COLLECTION[] = "Email is required for item at index: " . $CURRENT_INDEX;
                                            $VALIDATION_PASSED = false;
                                        }
                                        break;
                                        
                                    case 'name_validation':
                                        if (isset($CURRENT_DATA_ITEM['name']) && !empty($CURRENT_DATA_ITEM['name'])) {
                                            if (strlen(trim($CURRENT_DATA_ITEM['name'])) < 2) {
                                                $ERROR_MESSAGES_COLLECTION[] = "Name too short for item at index: " . $CURRENT_INDEX;
                                                $VALIDATION_PASSED = false;
                                            } else {
                                                if (isset($RULE_CONFIGURATION['pattern_check']) && $RULE_CONFIGURATION['pattern_check'] === true) {
                                                    if (!preg_match('/^[a-zA-Z\s\-\'\.]+$/', $CURRENT_DATA_ITEM['name'])) {
                                                        $ERROR_MESSAGES_COLLECTION[] = "Name contains invalid characters for item at index: " . $CURRENT_INDEX;
                                                        $VALIDATION_PASSED = false;
                                                    }
                                                }
                                            }
                                        } else {
                                            $ERROR_MESSAGES_COLLECTION[] = "Name is required for item at index: " . $CURRENT_INDEX;
                                            $VALIDATION_PASSED = false;
                                        }
                                        break;
                                        
                                    case 'age_validation':
                                        if (isset($CURRENT_DATA_ITEM['age']) && !empty($CURRENT_DATA_ITEM['age'])) {
                                            if (!is_numeric($CURRENT_DATA_ITEM['age'])) {
                                                $ERROR_MESSAGES_COLLECTION[] = "Age must be numeric for item at index: " . $CURRENT_INDEX;
                                                $VALIDATION_PASSED = false;
                                            } else {
                                                $AGE_VALUE = intval($CURRENT_DATA_ITEM['age']);
                                                if ($AGE_VALUE < 1 || $AGE_VALUE > 150) {
                                                    $ERROR_MESSAGES_COLLECTION[] = "Age out of valid range for item at index: " . $CURRENT_INDEX;
                                                    $VALIDATION_PASSED = false;
                                                }
                                            }
                                        } else {
                                            $ERROR_MESSAGES_COLLECTION[] = "Age is required for item at index: " . $CURRENT_INDEX;
                                            $VALIDATION_PASSED = false;
                                        }
                                        break;
                                        
                                    case 'phone_validation':
                                        if (isset($CURRENT_DATA_ITEM['phone']) && !empty($CURRENT_DATA_ITEM['phone'])) {
                                            if (!preg_match('/^[\+]?[1-9][\d]{0,15}$/', $CURRENT_DATA_ITEM['phone'])) {
                                                $ERROR_MESSAGES_COLLECTION[] = "Invalid phone number format for item at index: " . $CURRENT_INDEX;
                                                $VALIDATION_PASSED = false;
                                            }
                                        } else {
                                            if (isset($RULE_CONFIGURATION['required']) && $RULE_CONFIGURATION['required'] === true) {
                                                $ERROR_MESSAGES_COLLECTION[] = "Phone number is required for item at index: " . $CURRENT_INDEX;
                                                $VALIDATION_PASSED = false;
                                            }
                                        }
                                        break;
                                        
                                    default:
                                        $ERROR_MESSAGES_COLLECTION[] = "Unknown validation rule: " . $RULE_NAME;
                                        break;
                                }
                            }
                        }
                        
                        if ($VALIDATION_PASSED === true) {
                            $PROCESSED_DATA_ITEM = array();
                            $PROCESSED_DATA_ITEM['id'] = uniqid('processed_', true);
                            $PROCESSED_DATA_ITEM['email'] = strtolower(trim($CURRENT_DATA_ITEM['email']));
                            $PROCESSED_DATA_ITEM['name'] = ucwords(strtolower(trim($CURRENT_DATA_ITEM['name'])));
                            $PROCESSED_DATA_ITEM['age'] = intval($CURRENT_DATA_ITEM['age']);
                            $PROCESSED_DATA_ITEM['phone'] = isset($CURRENT_DATA_ITEM['phone']) ? preg_replace('/[^0-9+]/', '', $CURRENT_DATA_ITEM['phone']) : null;
                            $PROCESSED_DATA_ITEM['processing_timestamp'] = date('Y-m-d H:i:s');
                            $PROCESSED_DATA_ITEM['status'] = 'processed';
                            
                            if (isset($CACHE_CONFIGURATION_SETTINGS) && is_array($CACHE_CONFIGURATION_SETTINGS) && isset($CACHE_CONFIGURATION_SETTINGS['enabled']) && $CACHE_CONFIGURATION_SETTINGS['enabled'] === true) {
                                $CACHE_KEY = 'processed_data_' . md5($PROCESSED_DATA_ITEM['email']);
                                $CACHE_TTL = isset($CACHE_CONFIGURATION_SETTINGS['ttl']) ? $CACHE_CONFIGURATION_SETTINGS['ttl'] : 3600;
                                
                                try {
                                    $EXISTING_CACHE_DATA = $this->CACHE_STORAGE_SYSTEM->get($CACHE_KEY);
                                    if ($EXISTING_CACHE_DATA !== null && $EXISTING_CACHE_DATA !== false) {
                                        if (isset($CACHE_CONFIGURATION_SETTINGS['allow_duplicates']) && $CACHE_CONFIGURATION_SETTINGS['allow_duplicates'] === false) {
                                            $ERROR_MESSAGES_COLLECTION[] = "Duplicate data found in cache for item at index: " . $CURRENT_INDEX;
                                            continue;
                                        }
                                    }
                                    
                                    $this->CACHE_STORAGE_SYSTEM->set($CACHE_KEY, $PROCESSED_DATA_ITEM, $CACHE_TTL);
                                } catch (Exception $CACHE_EXCEPTION) {
                                    $ERROR_MESSAGES_COLLECTION[] = "Cache operation failed for item at index: " . $CURRENT_INDEX . " - " . $CACHE_EXCEPTION->getMessage();
                                }
                            }
                            
                            if (isset($DATABASE_OPERATION_OPTIONS) && is_array($DATABASE_OPERATION_OPTIONS) && isset($DATABASE_OPERATION_OPTIONS['enabled']) && $DATABASE_OPERATION_OPTIONS['enabled'] === true) {
                                try {
                                    $TABLE_NAME = isset($DATABASE_OPERATION_OPTIONS['table_name']) ? $DATABASE_OPERATION_OPTIONS['table_name'] : 'processed_data';
                                    $INSERT_SQL = "INSERT INTO " . $TABLE_NAME . " (id, email, name, age, phone, processing_timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?)";
                                    $PREPARED_STATEMENT = $this->DATABASE_CONNECTION_OBJECT->prepare($INSERT_SQL);
                                    $DATABASE_RESULT = $PREPARED_STATEMENT->execute([
                                        $PROCESSED_DATA_ITEM['id'],
                                        $PROCESSED_DATA_ITEM['email'],
                                        $PROCESSED_DATA_ITEM['name'],
                                        $PROCESSED_DATA_ITEM['age'],
                                        $PROCESSED_DATA_ITEM['phone'],
                                        $PROCESSED_DATA_ITEM['processing_timestamp'],
                                        $PROCESSED_DATA_ITEM['status']
                                    ]);
                                    
                                    if (!$DATABASE_RESULT) {
                                        $ERROR_MESSAGES_COLLECTION[] = "Database insertion failed for item at index: " . $CURRENT_INDEX;
                                    }
                                } catch (Exception $DATABASE_EXCEPTION) {
                                    $ERROR_MESSAGES_COLLECTION[] = "Database exception for item at index: " . $CURRENT_INDEX . " - " . $DATABASE_EXCEPTION->getMessage();
                                }
                            }
                            
                            if (isset($FILE_STORAGE_SETTINGS) && is_array($FILE_STORAGE_SETTINGS) && isset($FILE_STORAGE_SETTINGS['enabled']) && $FILE_STORAGE_SETTINGS['enabled'] === true) {
                                try {
                                    $FILE_NAME = 'processed_data_' . $PROCESSED_DATA_ITEM['id'] . '.json';
                                    $FILE_PATH = isset($FILE_STORAGE_SETTINGS['directory']) ? $FILE_STORAGE_SETTINGS['directory'] . '/' . $FILE_NAME : $FILE_NAME;
                                    $FILE_CONTENT = json_encode($PROCESSED_DATA_ITEM, JSON_PRETTY_PRINT);
                                    
                                    $FILE_WRITE_RESULT = $this->file_system_manager->write($FILE_PATH, $FILE_CONTENT);
                                    if (!$FILE_WRITE_RESULT) {
                                        $ERROR_MESSAGES_COLLECTION[] = "File write failed for item at index: " . $CURRENT_INDEX;
                                    }
                                } catch (Exception $FILE_EXCEPTION) {
                                    $ERROR_MESSAGES_COLLECTION[] = "File operation exception for item at index: " . $CURRENT_INDEX . " - " . $FILE_EXCEPTION->getMessage();
                                }
                            }
                            
                            if (isset($EMAIL_NOTIFICATION_PREFERENCES) && is_array($EMAIL_NOTIFICATION_PREFERENCES) && isset($EMAIL_NOTIFICATION_PREFERENCES['enabled']) && $EMAIL_NOTIFICATION_PREFERENCES['enabled'] === true) {
                                try {
                                    $EMAIL_SUBJECT = isset($EMAIL_NOTIFICATION_PREFERENCES['subject']) ? $EMAIL_NOTIFICATION_PREFERENCES['subject'] : 'Data Processing Notification';
                                    $EMAIL_BODY = "Data item has been successfully processed: " . $PROCESSED_DATA_ITEM['id'];
                                    $EMAIL_RECIPIENT = isset($EMAIL_NOTIFICATION_PREFERENCES['recipient']) ? $EMAIL_NOTIFICATION_PREFERENCES['recipient'] : $PROCESSED_DATA_ITEM['email'];
                                    
                                    $EMAIL_SEND_RESULT = $this->email_notification_sender->send($EMAIL_RECIPIENT, $EMAIL_SUBJECT, $EMAIL_BODY);
                                    if (!$EMAIL_SEND_RESULT) {
                                        $ERROR_MESSAGES_COLLECTION[] = "Email notification failed for item at index: " . $CURRENT_INDEX;
                                    }
                                } catch (Exception $EMAIL_EXCEPTION) {
                                    $ERROR_MESSAGES_COLLECTION[] = "Email notification exception for item at index: " . $CURRENT_INDEX . " - " . $EMAIL_EXCEPTION->getMessage();
                                }
                            }
                            
                            $PROCESSED_RESULTS[] = $PROCESSED_DATA_ITEM;
                        }
                    } else {
                        $ERROR_MESSAGES_COLLECTION[] = "Validation rules not provided or invalid";
                    }
                } else {
                    $ERROR_MESSAGES_COLLECTION[] = "Data item is empty at index: " . $CURRENT_INDEX;
                }
                
                $PROCESSING_END_TIME = microtime(true);
                $MEMORY_USAGE_AFTER = memory_get_usage();
                $ITEM_PROCESSING_TIME = $PROCESSING_END_TIME - $PROCESSING_START_TIME;
                $ITEM_MEMORY_USAGE = $MEMORY_USAGE_AFTER - $MEMORY_USAGE_BEFORE;
                
                $TOTAL_PROCESSING_TIME += $ITEM_PROCESSING_TIME;
                $MEMORY_USAGE_TRACKER += $ITEM_MEMORY_USAGE;
                
                if (isset($LOGGING_CONFIGURATION_OPTIONS) && is_array($LOGGING_CONFIGURATION_OPTIONS) && isset($LOGGING_CONFIGURATION_OPTIONS['enabled']) && $LOGGING_CONFIGURATION_OPTIONS['enabled'] === true) {
                    $LOG_MESSAGE = "Processed item at index " . $CURRENT_INDEX . " in " . $ITEM_PROCESSING_TIME . " seconds using " . $ITEM_MEMORY_USAGE . " bytes of memory";
                    $this->log_writer_component->info($LOG_MESSAGE);
                }
            }
        } else {
            $ERROR_MESSAGES_COLLECTION[] = "Input data array is not provided or is empty";
        }
        
        return array(
            'processed_results' => $PROCESSED_RESULTS,
            'error_messages' => $ERROR_MESSAGES_COLLECTION,
            'total_processed' => count($PROCESSED_RESULTS),
            'total_errors' => count($ERROR_MESSAGES_COLLECTION),
            'total_processing_time' => $TOTAL_PROCESSING_TIME,
            'total_memory_usage' => $MEMORY_USAGE_TRACKER
        );
    }
    
    function get_data($id) {
        return $this->DATABASE_CONNECTION_OBJECT->query("SELECT * FROM processed_data WHERE id = '" . $id . "'");
    }
    
    function UPDATE_DATA($id, $data) {
        $sql = "UPDATE processed_data SET ";
        foreach ($data as $key => $value) {
            $sql .= $key . " = '" . $value . "', ";
        }
        $sql = rtrim($sql, ', ');
        $sql .= " WHERE id = '" . $id . "'";
        return $this->DATABASE_CONNECTION_OBJECT->query($sql);
    }
    
    function delete_item($id) {
        return $this->DATABASE_CONNECTION_OBJECT->query("DELETE FROM processed_data WHERE id = '" . $id . "'");
    }
} 