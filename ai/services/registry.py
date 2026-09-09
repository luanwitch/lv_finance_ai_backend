from .agents.anomaly import AnomalyDetectorAgent
from .agents.assistant import FinancialAssistantAgent
from .agents.budget import BudgetPlannerAgent
from .agents.coach import CoachAgent
from .agents.debt import DebtAnalyzerAgent
from .agents.goals import GoalsAgent
from .agents.investments import InvestmentAgent
from .agents.invoice import InvoiceAgent

AGENTS = (
    FinancialAssistantAgent,
    BudgetPlannerAgent,
    GoalsAgent,
    AnomalyDetectorAgent,
    InvestmentAgent,
    DebtAnalyzerAgent,
    CoachAgent,
    InvoiceAgent
)
