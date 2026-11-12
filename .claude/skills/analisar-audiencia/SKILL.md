### `.claude/skills/analisar-audiencia/SKILL.md`

```markdown
---
name: analisar-audiencia
description: Analisa transcrições de audiências, organiza os depoimentos, identifica pontos relevantes, contradições e informações importantes. Use quando o usuário solicitar análise de uma audiência ou depoimento.
---

# Análise de audiência

Você é responsável por analisar o conteúdo de uma transcrição de audiência.

## Entrada

O usuário poderá informar:

- O caminho de uma transcrição.
- O nome de uma transcrição existente.
- Uma transcrição diretamente na conversa.

## Procedimento

1. Localize a transcrição.
2. Leia o conteúdo integralmente.
3. Preserve a ordem cronológica.
4. Identifique os participantes quando houver evidências explícitas.
5. Separe perguntas e respostas quando possível.
6. Identifique os principais assuntos discutidos.
7. Identifique divergências entre declarações.
8. Preserve timestamps relevantes.
9. Diferencie fatos documentados de alegações.
10. Indique trechos incompletos ou de baixa confiança.

## Estrutura da análise

# Identificação

- Arquivo analisado:
- Duração:
- Idioma:

# Resumo da audiência

Apresente um resumo objetivo.

# Participantes

Liste apenas os participantes identificáveis pelo conteúdo.

# Depoimentos

Organize os depoimentos por participante, quando possível.

# Pontos relevantes

Liste os assuntos mais importantes.

# Divergências identificadas

Apresente divergências entre declarações, indicando os timestamps.

# Trechos importantes

Liste trechos relevantes com seus timestamps.

# Pontos que precisam de conferência

Identifique palavras, nomes e trechos que possam ter sido transcritos incorretamente.

# Conclusão

Apresente uma síntese objetiva sem extrapolar o conteúdo.

## Regras de segurança e precisão

- Não invente informações.
- Não atribua falas sem evidência.
- Não trate alegações como fatos comprovados.
- Não altere o sentido dos depoimentos.
- Não apresente conclusões jurídicas definitivas.
- Informe quando a qualidade da transcrição limitar a análise.
```
