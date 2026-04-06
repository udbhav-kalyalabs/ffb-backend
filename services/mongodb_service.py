"""
MongoDB service for storing and retrieving analysis results
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class MongoDBService:
    """Service for managing analysis data in MongoDB"""
    
    def __init__(self):
        """Initialize MongoDB client"""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
        self._connected = False
    
    async def connect(self):
        """Connect to MongoDB"""
        if not self._connected:
            try:
                self.client = AsyncIOMotorClient(settings.MONGODB_URI)
                self.db = self.client[settings.MONGO_DATABASE]
                self.collection = self.db[settings.MONGO_COLLECTION]
                
                # Test connection
                await self.client.admin.command('ping')
                
                self._connected = True
                logger.info(f"Connected to MongoDB: {settings.MONGO_DATABASE}.{settings.MONGO_COLLECTION}")
                
                # Create indexes for better query performance
                await self._create_indexes()
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                raise
    
    async def _create_indexes(self):
        """Create indexes for optimized queries"""
        try:
            # Index on image_id for fast lookups
            await self.collection.create_index("image_id", unique=True)
            
            # Index on user_uuid for user queries
            await self.collection.create_index("user_uuid")
            
            # Index on created_at for time-based queries
            await self.collection.create_index([("created_at", -1)])
            
            # Compound index for user + time queries
            await self.collection.create_index([("user_uuid", 1), ("created_at", -1)])
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    async def save_analysis(
        self,
        image_id: str,
        user_uuid: str,
        filename: str,
        original_image_url: str,
        annotated_image_url: str,
        analysis_result: Dict[str, Any],
        latitude: Optional[str] = None,
        longitude: Optional[str] = None
    ) -> str:
        """
        Save analysis results to MongoDB
        
        Args:
            image_id: Unique identifier for the image
            user_uuid: User's unique identifier
            filename: Original filename
            original_image_url: S3 URL of original image
            annotated_image_url: S3 URL of annotated image
            analysis_result: Complete analysis results
            latitude: GPS latitude
            longitude: GPS longitude
            
        Returns:
            MongoDB document ID as string
        """
        try:
            await self.connect()
            
            document = {
                "image_id": image_id,
                "user_uuid": user_uuid,
                "filename": filename,
                "original_image_url": original_image_url,
                "annotated_image_url": annotated_image_url,
                "latitude": latitude,
                "longitude": longitude,
                "analysis": analysis_result,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.collection.insert_one(document)
            logger.info(f"Saved analysis for image_id={image_id}, mongo_id={result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {str(e)}")
            raise
    
    async def get_analysis_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis by image ID
        
        Args:
            image_id: Unique image identifier
            
        Returns:
            Analysis document or None if not found
        """
        try:
            await self.connect()
            
            document = await self.collection.find_one({"image_id": image_id})
            
            if document:
                document['_id'] = str(document['_id'])
                logger.info(f"Retrieved analysis for image_id={image_id}")
            else:
                logger.info(f"No analysis found for image_id={image_id}")
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {str(e)}")
            raise
    
    async def get_analyses_by_user(
        self,
        user_uuid: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all analyses for a specific user
        
        Args:
            user_uuid: User's unique identifier
            limit: Maximum number of results
            skip: Number of results to skip (for pagination)
            
        Returns:
            List of analysis documents
        """
        try:
            await self.connect()
            
            cursor = self.collection.find(
                {"user_uuid": user_uuid}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            for doc in documents:
                doc['_id'] = str(doc['_id'])
            
            logger.info(f"Retrieved {len(documents)} analyses for user={user_uuid}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve user analyses: {str(e)}")
            raise
    
    async def get_all_analyses(
        self,
        limit: int = 100,
        skip: int = 0,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending, 1 for ascending
    ) -> List[Dict[str, Any]]:
        """
        Get all analyses from database with pagination
        
        Args:
            limit: Maximum number of results
            skip: Number of results to skip
            sort_by: Field to sort by
            sort_order: -1 for descending, 1 for ascending
            
        Returns:
            List of analysis documents
        """
        try:
            await self.connect()
            
            cursor = self.collection.find().sort(sort_by, sort_order).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            for doc in documents:
                doc['_id'] = str(doc['_id'])
            
            logger.info(f"Retrieved {len(documents)} total analyses (skip={skip}, limit={limit})")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve all analyses: {str(e)}")
            raise
    
    async def count_all_analyses(self) -> int:
        """
        Get total count of all analyses in database
        
        Returns:
            Total number of analysis documents
        """
        try:
            await self.connect()
            
            count = await self.collection.count_documents({})
            logger.info(f"Total analyses in database: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count analyses: {str(e)}")
            raise
    
    async def count_user_analyses(self, user_uuid: str) -> int:
        """
        Get count of analyses for a specific user
        
        Args:
            user_uuid: User's unique identifier
            
        Returns:
            Number of analyses for the user
        """
        try:
            await self.connect()
            
            count = await self.collection.count_documents({"user_uuid": user_uuid})
            logger.info(f"User {user_uuid} has {count} analyses")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count user analyses: {str(e)}")
            raise
    
    async def get_analyses_with_filters(
        self,
        user_uuid: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        crop_type: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get analyses with optional filters
        
        Args:
            user_uuid: Filter by user (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            crop_type: Filter by crop type (optional)
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of filtered analysis documents
        """
        try:
            await self.connect()
            
            query = {}
            
            if user_uuid:
                query["user_uuid"] = user_uuid
            
            if start_date or end_date:
                query["created_at"] = {}
                if start_date:
                    query["created_at"]["$gte"] = start_date
                if end_date:
                    query["created_at"]["$lte"] = end_date
            
            if crop_type:
                query["analysis.crop_type"] = crop_type
            
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            for doc in documents:
                doc['_id'] = str(doc['_id'])
            
            logger.info(f"Retrieved {len(documents)} analyses with filters: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to retrieve filtered analyses: {str(e)}")
            raise
    
    async def delete_analysis(self, image_id: str) -> bool:
        """
        Delete an analysis by image ID
        
        Args:
            image_id: Unique image identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            await self.connect()
            
            result = await self.collection.delete_one({"image_id": image_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted analysis for image_id={image_id}")
                return True
            else:
                logger.info(f"No analysis found to delete for image_id={image_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete analysis: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with various statistics
        """
        try:
            await self.connect()
            
            total_analyses = await self.collection.count_documents({})
            
            # Get unique user count
            unique_users = await self.collection.distinct("user_uuid")
            
            # Get crop type distribution
            pipeline = [
                {"$group": {
                    "_id": "$analysis.crop_type",
                    "count": {"$sum": 1}
                }}
            ]
            crop_distribution = await self.collection.aggregate(pipeline).to_list(length=None)
            
            stats = {
                "total_analyses": total_analyses,
                "unique_users": len(unique_users),
                "crop_distribution": {item["_id"]: item["count"] for item in crop_distribution}
            }
            
            logger.info(f"Database statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            raise

# Singleton instance
mongodb_service = MongoDBService()

