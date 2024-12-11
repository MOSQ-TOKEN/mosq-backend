import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(DATABASE_URL)
        self.db = self.client["mosq_database"]
        self.users_collection = self.db["users"]
        self.tasks_collection = self.db["tasks"]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.client.close()


    async def save_new_user(self, uid, is_premium, invitor):
        """
        Create a new authenticated user in the database
        
        Args:
            uid (str): Unique user identifier
            invotor (str): User's referral
            premium (str): User's premium status
        """
        try:
            user_data = {
                        "uid": uid,
                        "invitor": invitor,
                        "is_premium": True if is_premium else False,
                        "referrals": 0,
                        "task_point": 150 if is_premium else 100,
                        "fleet": 3,
                        "checkin": datetime.now(),
                        "completed_tasks": [],
                        "handled": False,
                    }
            
            result = await self.users_collection.update_one(
                {"uid": uid},
                {"$setOnInsert": user_data},
                upsert=True
            )

            if result.matched_count == 0:
                # Increment the invitor's referral count
                await self.users_collection.update_one(
                    {"uid": invitor},
                    {
                        "$inc": {
                            "referrals": 1,
                            "gamePoints": 100,
                            }
                        }
                )
            
            return "User created successfully"
        except Exception as e:
            print(f"Error creating authenticated user: {e}")
            return "user creation failed"

    async def add_task(self, task_name, task_point, task_link, task_description=None):
        """
        Add a new task to the tasks collection and return full task details
        
        Args:
            task_name (str): Name of the task
            task_point (int): Points awarded for completing the task
            task_link (str): Link or reference for the task
            task_description (str, optional): Detailed description of the task
        
        Returns:
            dict: Full task details or None if operation fails
        """
        try:
            # Prepare task data with all possible fields
            task_data = {
                "task_name": task_name,
                "task_point": task_point,
                "task_link": task_link,
                "task_description": task_description or "",
                "created_at": datetime.now(),
                "completed_by": [],  # User IDs who have completed the task
                "handled": False,  # Default status for new tasks
                "active": True,  # Default status for new tasks
                "total_completions": 0,  # Track number of times task has been completed
                "last_completed_at": None,  # Timestamp of last task completion
            }
            
            # Perform upsert operation
            result = await self.tasks_collection.update_one(
                {"task_name": task_name},  # Filter: Match existing task by name
                {"$setOnInsert": task_data},
                upsert=True
            )
            
            # Retrieve the full task details
            task = await self.tasks_collection.find_one(
                {"task_name": task_name},
                # {"_id": 0}  # Exclude MongoDB's internal _id field
            )
            
            # Check if task was newly created or already existed
            if result.upserted_id:
                return {
                    "status": "created successfully",
                    "task_details": task
                }
            else:
                return {
                    "status": f"Task '{task_name}' already exists",
                    "task_details": task
                }
        
        except Exception as e:
            print(f"Error adding task: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    async def get_task_by_name(self, task_name):
        """
        Retrieve full details of a specific task by name
        
        Args:
            task_name (str): Name of the task to retrieve
        
        Returns:
            dict: Full task details or None if not found
        """
        try:
            task = await self.tasks_collection.find_one(
                {"task_name": task_name},
                {"_id": 0}  # Exclude MongoDB's internal _id field
            )
            
            return task
        except Exception as e:
            print(f"Error retrieving task: {e}")
            return None
    
    async def end_game(self, uid, game_point):
        """
        Mark a task as completed for a user and update their points, reducing their fleets
        
        Args:
            uid (str): User ID
            game_point (str): Name of the completed task
        """
        try:
            # Update user's points and completed tasks
            user_update = await self.users_collection.update_one(
                {"uid": uid},
                {
                    "$inc": {
                            "fleet": -1,
                            "task_point": game_point
                        }
                }
            )
            
            return f"Task completed. {game_point} points added."
        except Exception as e:
            print(f"Error completing task: {e}")
            return None
        
    async def task_complete(self, uid, task_name):
        """
        Mark a task as completed for a user and update their points
        
        Args:
            uid (str): User ID
            task_name (str): Name of the completed task
        """
        try:
            # Find the task to get its points
            task = await self.tasks_collection.find_one({"task_name": task_name})
            
            if not task:
                return "Task not found"
            
            task_point = task.get('task_point', 0)
            
            # Update user's points and completed tasks
            user_update = await self.users_collection.update_one(
                {"uid": uid},
                {
                    "$inc": {
                            "task_point": task_point
                        },
                    "$addToSet": {"completed_tasks": task_name}
                }
            )
            
            # Update task's completed_by list
            task_update = await self.tasks_collection.update_one(
                {"task_name": task_name},
                {"$addToSet": {"completed_by": uid}}
            )
            
            return f"Task completed. {task_point} points added."
        except Exception as e:
            print(f"Error completing task: {e}")
            return None
        
    async def check_in(self, uid):
        """
        Award points each day a user logs in and increment...
        
        Args:
            uid (str): User ID
        """
        try:
            # Find the user to get its points
            user = await self.users_collection.find_one({"uid": uid})
            
            if not user:
                return "User not found"
            
            # Calculate the number of days since last checkin

            today = datetime.now().date()

            # Convert last_checkin to date if it's a datetime
            last_checkin = user['checkin'].date()

            # Check if the user has already checked in today
            if last_checkin == today:
                user['_id'] = str(user['_id'])
                user['checkin'] = user['checkin'].isoformat()
                return user

            if last_checkin:
                days_since_checkin = (today - last_checkin).days
                
                # Award points based on the number of days since last checkin
                user_update = await self.users_collection.find_one_and_update(
                    {"uid": uid},
                    {
                        "$inc": {
                            "fleet": days_since_checkin
                        },
                        "$set": {"checkin": datetime.now().date()}
                    },
                    return_document=True # This ensures we get the updated document
                )
                

            # Convert ObjectId to string for JSON serialization
            user_update['_id'] = str(user_update['_id'])
            user_update['checkin'] = user_update['checkin'].isoformat()
            return user_update
        except Exception as e:
            print(f"Error checking in: {e}")
            return None

    async def fetch_all_tasks(self):
        """
        Fetch all available tasks
        
        Returns:
            List of tasks
        """
        try:
            tasks = await self.tasks_collection.find(
                {"active": True},
                {"_id": 0}
            ).to_list(length=None)
            
            return tasks
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            return []

    async def user_data(self, uid):
        """
        Retrieve a user's profile information
        
        Args:
            uid (str): User ID
        
        Returns:
            User profile data or None
        """
        try:
            result = await self.users_collection.find_one({"uid": uid})

            # Convert ObjectId to string for JSON serialization
            result['_id'] = str(result['_id'])
            result['checkin'] = result['checkin'].isoformat()

            return result
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return None
        
    async def get_all_users(self):
        """
        Retrieve a all user's profile information
        
        Args:
            null
        
        Returns:
            All User profiles or None
        """
        try:
            users = await self.users_collection.find().to_list(length=None)
            
            return users

            return result
        except Exception as e:
            print(f"Error retrieving all profiles: {e}")
            return None

    async def create_indexes(self):
        """
        Create indexes for efficient querying
        """
        try:
            # Create unique index for users collection
            await self.users_collection.create_index("uid", unique=True)
            await self.users_collection.create_index("email", unique=True)
            
            # Create index for tasks collection
            await self.tasks_collection.create_index("task_name", unique=True)
            
            print("Indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {e}")
