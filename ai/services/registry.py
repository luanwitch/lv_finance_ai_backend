from .agents.assistant import FinancialAssistantAgent
from .agents.budget import BudgetPlannerAgent
from .agents.goals import GoalsAgent
from .agents.anomaly import AnomalyDetectorAgent
from .agents.coach import CoachAgent
from .agents.investments import InvestmentAgent
from .agents.invoice import InvoiceAgent
from .agents.debt import DebtAnalyzerAgent

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