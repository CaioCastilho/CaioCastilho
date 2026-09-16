<div align="center">

  <!-- Exibição Principal do SVG Dinâmico Animado -->
  <img src="./perfil_animado.svg" alt="Caio Castilho - Dynamic Profile Terminal" width="100%" />

  <p align="center">
    <i>Terminal interativo com telemetria em tempo real atualizada diariamente via GitHub Actions &amp; Python.</i>
  </p>

  <p align="center">
    <a href="https://github.com/CaioCastilho">
      <img src="https://img.shields.io/badge/GitHub-CaioCastilho-00f0ff?style=flat-square&logo=github&logoColor=white" alt="GitHub" />
    </a>
    <img src="https://img.shields.io/badge/Status-Online-00ff9d?style=flat-square" alt="Status Online" />
    <img src="https://img.shields.io/badge/Automation-GitHub%20Actions-blueviolet?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions" />
    <img src="https://img.shields.io/badge/Engine-Python%203.11+-ffd43b?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+" />
  </p>

</div>

---

### ⚙️ Como funciona a arquitetura

Este perfil foi construído substituindo texto estático por um **único arquivo vetorial SVG animado** com CSS puro (`perfil_animado.svg`).

1. **Template Base (`template.svg`)**: Define a estrutura gráfica, janelas do terminal, badges, ícones e tags de animação CSS (`@keyframes`), contendo placeholders (`{{TOTAL_COMMITS}}`, `{{STARS}}`, `{{FOLLOWERS}}`, `{{PUBLIC_REPOS}}`, `{{LAST_UPDATED}}`).
2. **Motor de Dados (`generate.py`)**: Script em Python que consome a API do GitHub com headers autenticados, soma métricas reais e compila o SVG final.
3. **Orquestração (`.github/workflows/update.yml`)**: Workflow de CI/CD que executa à meia-noite todos os dias, gera o novo arquivo e commita as alterações via `github-actions[bot]`.

---

### 🚀 Executando localmente

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Execute o gerador de SVG
python generate.py

# 3. O arquivo 'perfil_animado.svg' será gerado/atualizado na raiz
```
