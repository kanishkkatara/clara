from typing import List
from sqlalchemy.orm import Session
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
        total = self.session.query(UserQuestionProgress)\
            .filter_by(user_id=self.user.id).count()
        correct = self.session.query(UserQuestionProgress)\
            .filter_by(user_id=self.user.id, is_correct=True).count()
        # TODO: derive timeStudied
        return StatsSchema(
            targetScore=getattr(self.user, 'target_score', None),
            timeStudied=0.0,
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
        answered = self.session.query(UserQuestionProgress)\
            .filter_by(user_id=self.user.id).count() or 1
        correct = self.session.query(UserQuestionProgress)\
            .filter_by(user_id=self.user.id, is_correct=True).count()
        pct = int(correct / answered * 100)
        return OverallSchema(
            quantitative=pct,
            verbal=0,
            ir=0,
            average=pct
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