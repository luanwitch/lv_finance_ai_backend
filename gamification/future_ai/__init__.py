"""Ponto de extensão para uma futura camada de IA (NÃO implementado).

Esta versão da gamificação é 100% determinística. Quando a camada de
IA for adicionada, ela deverá:

1. Consumir as métricas já calculadas
   (`gamification.services.metrics_service.compute_metrics`) e o
   histórico (`XPTransaction`) — nada precisa ser reescrito;
2. Ser acionada APÓS `handle_event` / `run_periodic_checks`, por
   exemplo gerando insights personalizados ou sugerindo desafios,
   sem alterar as regras determinísticas de XP;
3. Nunca conceder XP diretamente: qualquer XP continuará passando por
   `xp_service.award_xp` com chave de idempotência.

Módulos candidatos: recomendações de desafios, mensagens motivacionais
do perfil e diagnóstico financeiro conversacional.
"""
