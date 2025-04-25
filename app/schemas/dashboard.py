from typing import Any, List, Optional
from pydantic import BaseModel

class StatsSchema(BaseModel):
    targetScore: Optional[int]
    timeStudied: float  # hours
    questionsCompleted: int

class StudyPlanItem(BaseModel):
    id: str
    title: str
    description: Any
    completed: bool
    total: int
    difficulty: int
    estimatedTime: int  # minutes
    topics: List[str]
    icon: Optional[str]

class OverallSchema(BaseModel):
    quantitative: int
    verbal: int
    di: int
    average: int

class PerformanceDataItem(BaseModel):
    week: str
    correct: int
    incorrect: int

class TopicPerformanceItem(BaseModel):
    topic: str
    correct: int
    total: int

class DashboardResponse(BaseModel):
    stats: StatsSchema
    studyPlan: List[StudyPlanItem]
    overallProgress: OverallSchema
    performanceData: List[PerformanceDataItem]
    topicPerformance: List[TopicPerformanceItem]