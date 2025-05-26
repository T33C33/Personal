class AuthManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.current_user = None
    
    def login(self, username, password):
        if not username or not password:
            return False, "Please enter both username and password"
        
        user = self.db_manager.execute_query(
            "SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
            (username, password),
            fetchone=True
        )
        
        if user:
            self.current_user = {"id": user[0], "username": user[1], "role": user[2]}
            return True, "Login successful"
        else:
            return False, "Invalid username or password"
    
    def register(self, username, password, confirm_password, role):
        # Validate inputs
        if not username or not password or not confirm_password:
            return False, "Please fill in all fields"
        
        if password != confirm_password:
            return False, "Passwords do not match"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        # Check if username already exists
        user_count = self.db_manager.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?", 
            (username,),
            fetchone=True
        )[0]
        
        if user_count > 0:
            return False, "Username already exists"
        
        # Insert new user
        try:
            self.db_manager.execute_query(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                (username, password, role)
            )
            return True, "Registration successful"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def logout(self):
        self.current_user = None
        return True
    
    def get_all_users(self):
        """Get all users from the database"""
        return self.db_manager.execute_query(
            "SELECT id, username, role, created_at FROM users ORDER BY username"
        )
    
    def delete_user(self, user_id):
        """Delete a user from the database"""
        # Check if user is the current user
        if self.current_user and str(self.current_user["id"]) == str(user_id):
            return False, "Cannot delete your own account"
        
        # Check if user is the last admin
        if self.db_manager.execute_query(
            "SELECT role FROM users WHERE id = ?", 
            (user_id,), 
            fetchone=True
        )[0] == "admin":
            admin_count = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM users WHERE role = 'admin'", 
                fetchone=True
            )[0]
            
            if admin_count <= 1:
                return False, "Cannot delete the last admin account"
        
        # Delete user
        try:
            self.db_manager.execute_query(
                "DELETE FROM users WHERE id = ?", 
                (user_id,)
            )
            return True, "User deleted successfully"
        except Exception as e:
            return False, f"Failed to delete user: {str(e)}"
    
    def change_password(self, user_id, current_password, new_password, confirm_password):
        """Change a user's password"""
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            return False, "Please fill in all fields"
        
        if new_password != confirm_password:
            return False, "New passwords do not match"
        
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters long"
        
        # Check current password
        user = self.db_manager.execute_query(
            "SELECT id FROM users WHERE id = ? AND password = ?", 
            (user_id, current_password),
            fetchone=True
        )
        
        if not user:
            return False, "Current password is incorrect"
        
        # Update password
        try:
            self.db_manager.execute_query(
                "UPDATE users SET password = ? WHERE id = ?", 
                (new_password, user_id)
            )
            return True, "Password changed successfully"
        except Exception as e:
            return False, f"Failed to change password: {str(e)}"