"""Prompts y PromptBuilder del Bounded Context de Chat y Asistente Financiero"""

from collections.abc import Sequence
from decimal import Decimal
from backend.core.prompts import GLOBAL_SECURITY_GUARDRAILS
from backend.modules.transactions.models import Transaction

EXPENSE_PARSER_SYSTEM_PROMPT = (
    "Eres un extractor especializado en transacciones financieras para una billetera digital. "
    "Tu tarea es analizar el texto en lenguaje natural del usuario y extraer con exactitud: "
    "monto numérico (amount), categoría representativa (category) y concepto (description). "
    "Categorías sugeridas: Alimentación, Transporte, Salud, Entretenimiento, Servicios, Compras, Otros."
)

FINANCIAL_ADVISOR_SYSTEM_PROMPT = (
    "Eres el asistente financiero inteligente de SmartWallet AI. "
    "Tu rol es analizar y responder preguntas sobre los gastos, ingresos y saldo del usuario "
    "de forma profesional, empática, concisa y precisa.\n\n"
    f"{GLOBAL_SECURITY_GUARDRAILS}"
)


class FinancialPromptBuilder:
    """Construye prompts modulares para grounding financiero y RAG"""

    @staticmethod
    def build_rag_prompt(
        balance: Decimal,
        currency: str,
        transactions: Sequence[Transaction],
        question: str,
    ) -> str:
        """Ensambla el prompt compositivo combinando saldo real, transacciones recuperadas y consulta"""
        if transactions:
            tx_lines = [
                f"- Fecha: {tx.created_at.strftime('%Y-%m-%d')} | Tipo: {tx.type.value} | "
                f"Categoría: {tx.category} | Monto: ${tx.amount} | Descripción: {tx.description}"
                for tx in transactions
            ]
            transactions_context = "\n".join(tx_lines)
        else:
            transactions_context = (
                "No se encontraron transacciones previas relacionadas con esta consulta."
            )

        return (
            f"=== CONTEXTO FINANCIERO DEL USUARIO ===\n"
            f"- Saldo actual disponible: ${balance} {currency}\n\n"
            f"=== MOVIMIENTOS HISTÓRICOS RECUPERADOS (EVIDENCIA) ===\n"
            f"{transactions_context}\n\n"
            f"=== CONSULTA DEL USUARIO ===\n"
            f"{question}"
        )