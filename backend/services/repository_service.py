"""
Repository 서비스
단일 책임: Repository 비즈니스 로직 처리
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import uuid

from ..models.repository import Repository, RepositoryMember
from ..models.user import User
from ..schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    RepositoryMemberCreate,
    RepositoryMemberUpdate
)


class RepositoryService:
    """Repository 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_repository(db: Session, repo_data: RepositoryCreate, owner_id: str) -> Repository:
        """
        새로운 Repository 생성
        
        Args:
            db: 데이터베이스 세션
            repo_data: Repository 생성 데이터
            owner_id: Repository 소유자 ID
            
        Returns:
            생성된 Repository 객체
        """
        db_repo = Repository(
            id=uuid.uuid4(),
            name=repo_data.name,
            description=repo_data.description,
            url=repo_data.url,
            owner_id=uuid.UUID(owner_id),
            is_public=repo_data.is_public,
            status="pending",  # 초기 상태는 pending
            vectordb_status="pending"
        )
        
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
        
        return db_repo

    @staticmethod
    def get_repository(db: Session, repo_id: str) -> Optional[Repository]:
        """Repository 조회"""
        return db.query(Repository).filter(Repository.id == uuid.UUID(repo_id)).first()

    @staticmethod
    def get_user_repositories(db: Session, user_id: str) -> List[Repository]:
        """
        사용자가 접근 가능한 모든 Repository 조회
        (소유한 Repository + 멤버로 참여한 Repository)
        """
        user_uuid = uuid.UUID(user_id)
        
        # 소유한 Repository 또는 멤버로 참여한 Repository
        repositories = db.query(Repository).outerjoin(
            RepositoryMember,
            Repository.id == RepositoryMember.repository_id
        ).filter(
            or_(
                Repository.owner_id == user_uuid,
                RepositoryMember.user_id == user_uuid
            )
        ).distinct().all()
        
        return repositories

    @staticmethod
    def update_repository(
        db: Session,
        repo_id: str,
        repo_data: RepositoryUpdate
    ) -> Optional[Repository]:
        """Repository 업데이트"""
        db_repo = RepositoryService.get_repository(db, repo_id)
        if not db_repo:
            return None
        
        update_data = repo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_repo, field, value)
        
        db_repo.updated_at = datetime.now()
        db.commit()
        db.refresh(db_repo)
        
        return db_repo

    @staticmethod
    def delete_repository(db: Session, repo_id: str) -> bool:
        """Repository 삭제"""
        db_repo = RepositoryService.get_repository(db, repo_id)
        if not db_repo:
            return False
        
        db.delete(db_repo)
        db.commit()
        return True

    @staticmethod
    def update_repository_status(
        db: Session,
        repo_id: str,
        status: str,
        vectordb_status: Optional[str] = None
    ) -> Optional[Repository]:
        """Repository 상태 업데이트 (Celery Task에서 호출)"""
        db_repo = RepositoryService.get_repository(db, repo_id)
        if not db_repo:
            return None
        
        db_repo.status = status
        if vectordb_status:
            db_repo.vectordb_status = vectordb_status
        
        db_repo.last_sync = datetime.now()
        db.commit()
        db.refresh(db_repo)
        
        return db_repo

    @staticmethod
    def update_file_count(db: Session, repo_id: str, file_count: int) -> Optional[Repository]:
        """파일 개수 업데이트 (파싱 완료 후 호출)"""
        db_repo = RepositoryService.get_repository(db, repo_id)
        if not db_repo:
            return None

        db_repo.file_count = file_count
        db.commit()
        db.refresh(db_repo)

        return db_repo

    @staticmethod
    def increment_collections_count(db: Session, repo_id: str) -> Optional[Repository]:
        """컬렉션 개수 증가 (벡터 컬렉션 생성 후 호출)"""
        db_repo = RepositoryService.get_repository(db, repo_id)
        if not db_repo:
            return None

        db_repo.collections_count = (db_repo.collections_count or 0) + 1
        db.commit()
        db.refresh(db_repo)

        return db_repo

    @staticmethod
    def check_user_permission(
        db: Session,
        repo_id: str,
        user_id: str,
        required_role: Optional[str] = None
    ) -> bool:
        """
        사용자의 Repository 접근 권한 확인
        
        Args:
            db: 데이터베이스 세션
            repo_id: Repository ID
            user_id: 사용자 ID
            required_role: 필요한 역할 (None이면 접근만 확인)
        
        Returns:
            권한 여부
        """
        user_uuid = uuid.UUID(user_id)
        repo_uuid = uuid.UUID(repo_id)
        
        # 소유자 확인
        repo = db.query(Repository).filter(Repository.id == repo_uuid).first()
        if repo and repo.owner_id == user_uuid:
            return True
        
        # 멤버 확인
        member = db.query(RepositoryMember).filter(
            and_(
                RepositoryMember.repository_id == repo_uuid,
                RepositoryMember.user_id == user_uuid
            )
        ).first()
        
        if not member:
            return False
        
        # 역할 확인
        if required_role:
            role_hierarchy = {"viewer": 0, "member": 1, "admin": 2}
            user_role_level = role_hierarchy.get(member.role, 0)
            required_role_level = role_hierarchy.get(required_role, 0)
            return user_role_level >= required_role_level
        
        return True


class RepositoryMemberService:
    """Repository Member 관련 비즈니스 로직 처리"""

    @staticmethod
    def add_member(
        db: Session,
        repo_id: str,
        member_data: RepositoryMemberCreate
    ) -> RepositoryMember:
        """Repository에 멤버 추가"""
        db_member = RepositoryMember(
            id=uuid.uuid4(),
            repository_id=uuid.UUID(repo_id),
            user_id=uuid.UUID(member_data.user_id),
            role=member_data.role
        )
        
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        
        return db_member

    @staticmethod
    def get_repository_members(db: Session, repo_id: str) -> List[RepositoryMember]:
        """Repository의 모든 멤버 조회"""
        return db.query(RepositoryMember).filter(
            RepositoryMember.repository_id == uuid.UUID(repo_id)
        ).all()

    @staticmethod
    def update_member_role(
        db: Session,
        member_id: str,
        role_data: RepositoryMemberUpdate
    ) -> Optional[RepositoryMember]:
        """멤버 역할 업데이트"""
        db_member = db.query(RepositoryMember).filter(
            RepositoryMember.id == uuid.UUID(member_id)
        ).first()
        
        if not db_member:
            return None
        
        db_member.role = role_data.role
        db.commit()
        db.refresh(db_member)
        
        return db_member

    @staticmethod
    def remove_member(db: Session, member_id: str) -> bool:
        """Repository에서 멤버 제거"""
        db_member = db.query(RepositoryMember).filter(
            RepositoryMember.id == uuid.UUID(member_id)
        ).first()
        
        if not db_member:
            return False
        
        db.delete(db_member)
        db.commit()
        return True

    @staticmethod
    def get_member_by_user(
        db: Session,
        repo_id: str,
        user_id: str
    ) -> Optional[RepositoryMember]:
        """특정 사용자의 멤버 정보 조회"""
        return db.query(RepositoryMember).filter(
            and_(
                RepositoryMember.repository_id == uuid.UUID(repo_id),
                RepositoryMember.user_id == uuid.UUID(user_id)
            )
        ).first()
