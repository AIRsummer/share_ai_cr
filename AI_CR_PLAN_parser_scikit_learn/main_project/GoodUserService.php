<?php

/**
 * 用户服务类 - 清洁代码示例
 * 遵循SOLID原则和最佳实践
 */
class UserService
{
    private UserRepository $userRepository;
    private EmailService $emailService;
    private ValidationService $validator;
    private CacheService $cache;
    
    public function __construct(
        UserRepository $userRepository,
        EmailService $emailService,
        ValidationService $validator,
        CacheService $cache
    ) {
        $this->userRepository = $userRepository;
        $this->emailService = $emailService;
        $this->validator = $validator;
        $this->cache = $cache;
    }
    
    /**
     * 创建新用户
     * 
     * @param UserData $userData 用户数据
     * @return User 创建的用户
     * @throws InvalidUserDataException
     * @throws UserExistsException
     */
    public function createUser(UserData $userData): User
    {
        $this->validateUserData($userData);
        $this->ensureUserDoesNotExist($userData->getEmail());
        
        $user = new User(
            $userData->getEmail(),
            $userData->getName(),
            $userData->getAge(),
            $userData->getPhone()
        );
        
        $savedUser = $this->userRepository->save($user);
        $this->cache->invalidateUserCache($savedUser->getEmail());
        $this->sendWelcomeEmail($savedUser);
        
        return $savedUser;
    }
    
    /**
     * 根据ID获取用户
     * 
     * @param string $userId 用户ID
     * @return User|null
     */
    public function getUserById(string $userId): ?User
    {
        $cacheKey = "user_{$userId}";
        $cachedUser = $this->cache->get($cacheKey);
        
        if ($cachedUser !== null) {
            return $cachedUser;
        }
        
        $user = $this->userRepository->findById($userId);
        
        if ($user !== null) {
            $this->cache->set($cacheKey, $user, 3600);
        }
        
        return $user;
    }
    
    /**
     * 更新用户信息
     * 
     * @param string $userId 用户ID
     * @param UserData $userData 更新的用户数据
     * @return User 更新后的用户
     * @throws UserNotFoundException
     * @throws InvalidUserDataException
     */
    public function updateUser(string $userId, UserData $userData): User
    {
        $user = $this->getUserById($userId);
        
        if ($user === null) {
            throw new UserNotFoundException("User with ID {$userId} not found");
        }
        
        $this->validateUserData($userData);
        
        $user->updateInfo(
            $userData->getName(),
            $userData->getAge(),
            $userData->getPhone()
        );
        
        $updatedUser = $this->userRepository->save($user);
        $this->cache->invalidateUserCache($user->getEmail());
        
        return $updatedUser;
    }
    
    /**
     * 删除用户
     * 
     * @param string $userId 用户ID
     * @return bool 删除是否成功
     * @throws UserNotFoundException
     */
    public function deleteUser(string $userId): bool
    {
        $user = $this->getUserById($userId);
        
        if ($user === null) {
            throw new UserNotFoundException("User with ID {$userId} not found");
        }
        
        $deleted = $this->userRepository->delete($userId);
        
        if ($deleted) {
            $this->cache->invalidateUserCache($user->getEmail());
        }
        
        return $deleted;
    }
    
    /**
     * 验证用户数据
     * 
     * @param UserData $userData 用户数据
     * @throws InvalidUserDataException
     */
    private function validateUserData(UserData $userData): void
    {
        if (!$this->validator->isValidEmail($userData->getEmail())) {
            throw new InvalidUserDataException('Invalid email format');
        }
        
        if (!$this->validator->isValidName($userData->getName())) {
            throw new InvalidUserDataException('Invalid name format');
        }
        
        if (!$this->validator->isValidAge($userData->getAge())) {
            throw new InvalidUserDataException('Invalid age');
        }
        
        if (!$this->validator->isValidPhone($userData->getPhone())) {
            throw new InvalidUserDataException('Invalid phone number');
        }
    }
    
    /**
     * 确保用户不存在
     * 
     * @param string $email 邮箱地址
     * @throws UserExistsException
     */
    private function ensureUserDoesNotExist(string $email): void
    {
        $existingUser = $this->userRepository->findByEmail($email);
        
        if ($existingUser !== null) {
            throw new UserExistsException("User with email {$email} already exists");
        }
    }
    
    /**
     * 发送欢迎邮件
     * 
     * @param User $user 用户
     */
    private function sendWelcomeEmail(User $user): void
    {
        try {
            $this->emailService->sendWelcomeEmail(
                $user->getEmail(),
                $user->getName()
            );
        } catch (EmailServiceException $e) {
            // 记录错误但不阻止用户创建流程
            error_log("Failed to send welcome email to {$user->getEmail()}: " . $e->getMessage());
        }
    }
} 