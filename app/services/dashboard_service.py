from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.profile import UserProfile
from app.models.progress import UserQuestionProgress
from app.models.question import Question
from app.schemas.dashboard import (
    StatsSchema, StudyPlanItem, OverallSchema,
    PerformanceDataItem, TopicPerformanceItem, DashboardResponse
)

class DashboardService:
    def __init__(self, session: Session, user):
        self.session = session
        self.user = user

    def get_stats(self) -> StatsSchema:
        # total questions seen
        total = (
            self.session
                .query(UserQuestionProgress)
                .filter_by(user_id=self.user.id)
                .count()
        )

        # correct answers count (if you ever want it)
        correct = (
            self.session
                .query(UserQuestionProgress)
                .filter_by(user_id=self.user.id, is_correct=True)
                .count()
        )

        # fetch the profile row
        profile = (
            self.session
                .query(UserProfile)
                .filter_by(user_id=self.user.id)
                .first()
        )
        target_score = profile.target_score if profile else None
        total_secs = getattr(profile, "total_time", 0) or 0
        time_hours = round(total_secs / 3600.0, 2)

        # TODO: derive real timeStudied
        return StatsSchema(
            targetScore=target_score,
            timeStudied=time_hours,
            questionsCompleted=total
        )

    def get_study_plan(self) -> List[StudyPlanItem]:
        subq = self.session.query(UserQuestionProgress.question_id)\
            .filter_by(user_id=self.user.id).subquery()
        unanswered = self.session.query(Question)\
            .filter(~Question.id.in_(subq)).limit(4).all()
        plan = []
        for q in unanswered:
            plan.append(
                StudyPlanItem(
                    id=str(q.id),
                    title=q.type,
                    description=q.content,
                    completed=False,
                    total=len(q.options),
                    difficulty=q.difficulty,
                    estimatedTime=5,
                    topics=q.tags,
                    icon=None
                )
            )
        return plan

    def get_overall_progress(self) -> OverallSchema:
        """
        Compute percent‐correct per category by filtering on Question.type,
        then return each percentage along with their average.
        """
        user_id = self.user.id

        # Map each dashboard category to the question.type values in it
        category_type_map = {
            'quantitative': ['problem-solving'],
            'verbal': ['reading-comprehension', 'critical-reasoning'],
            'di': ['data-sufficiency', 'table-analysis', 'graphics-interpretation', 'two-part-analysis', 'multi-source-reasoning'],
        }

        stats: dict[str, int] = {}

        for category, types in category_type_map.items():        
            # total available in this category
            total_cat = (
                self.session.query(func.count(Question.id))
                .filter(Question.type.in_(types))
                .scalar()
                or 1
            )
            # total user has completed in this category
            completed_cat = (
                self.session.query(func.count(UserQuestionProgress.id))
                .join(Question, Question.id == UserQuestionProgress.question_id)
                .filter(
                    UserQuestionProgress.user_id == user_id,
                    Question.type.in_(types)
                )
                .scalar()
                or 0
            )
            stats[category] = int(completed_cat / total_cat * 100)

        # Compute an overall average across categories
                # 1) overall completed / total
        total_questions = (
            self.session.query(func.count(Question.id))
            .scalar()
            or 1
        )
        total_completed = (
            self.session.query(func.count(UserQuestionProgress.id))
            .filter(UserQuestionProgress.user_id == user_id)
            .scalar()
            or 0
        )
        stats['overall'] = int(total_completed / total_questions * 100)

        return OverallSchema(
            quantitative=stats.get('quantitative', 0),
            verbal=stats.get('verbal', 0),
            di=stats.get('di', 0),
            average=stats.get('overall', 0)
        )

    def get_performance_data(self) -> List[PerformanceDataItem]:
        # stub: replace with real query
        return []

    def get_topic_performance(self) -> List[TopicPerformanceItem]:
        # stub: replace with real query
        return []

    def get_dashboard(self) -> DashboardResponse:
        return DashboardResponse(
            stats=self.get_stats(),
            studyPlan=self.get_study_plan(),
            overallProgress=self.get_overall_progress(),
            performanceData=self.get_performance_data(),
            topicPerformance=self.get_topic_performance(),
        )

# alias for injection
dashboard_service = DashboardService