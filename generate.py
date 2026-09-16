#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
MOTOR PYTHON: Gerador de Perfil Animado Dinâmico para GitHub
==============================================================================
Autor: Caio Castilho
Descrição:
    Este script coleta estatísticas em tempo real da API pública do GitHub
    (seguidores, repositórios públicos, total de estrelas e total de commits),
    preenche o template SVG com animações CSS e gera o arquivo 'perfil_animado.svg'
    que é incorporado no README do perfil.
==============================================================================
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    print(
        "[ERRO] A biblioteca 'requests' não foi encontrada. "
        "Instale-a executando: pip install -r requirements.txt",
        file=sys.stderr
    )
    sys.exit(1)

# Garante suporte a UTF-8 no console mesmo no Windows
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("GitHubStatsGenerator")


class GitHubStatsFetcher:
    """Responsável por consumir os endpoints da API pública do GitHub."""

    BASE_URL = "https://api.github.com"

    def __init__(self, username: str, token: Optional[str] = None):
        self.username = username
        self.session = requests.Session()

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"Dynamic-Profile-Generator-{username}"
        }

        # Se houver token de autenticação (fornecido pelo GitHub Actions ou localmente),
        # inclui no cabeçalho para aumentar os limites de requisições (rate limits).
        if token:
            headers["Authorization"] = f"Bearer {token}"
            logger.info("Autenticação configurada com GITHUB_TOKEN.")
        else:
            logger.warning(
                "Nenhum GITHUB_TOKEN detectado. Operando em modo não-autenticado "
                "(limite reduzido de 60 requisições/hora)."
            )

        self.session.headers.update(headers)

    def get_user_profile(self) -> Dict[str, Any]:
        """Obtém dados gerais do usuário: seguidores, repositórios públicos e bio."""
        url = f"{self.BASE_URL}/users/{self.username}"
        logger.info(f"Buscando dados cadastrais de @{self.username}...")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Falha ao consultar perfil de @{self.username}: {e}")
            return {"followers": 0, "public_repos": 0}

    def get_stars_and_repos(self) -> Dict[str, int]:
        """Calcula o total de estrelas recebidas em todos os repositórios públicos do usuário."""
        url = f"{self.BASE_URL}/users/{self.username}/repos"
        params = {"per_page": 100, "type": "owner"}
        logger.info(f"Buscando repositórios e calculando estrelas de @{self.username}...")

        total_stars = 0
        repo_count = 0

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            repos = response.json()

            if isinstance(repos, list):
                for repo in repos:
                    # Conta apenas repositórios que não sejam forks para métrica fidedigna
                    if not repo.get("fork", False):
                        total_stars += repo.get("stargazers_count", 0)
                        repo_count += 1

            return {"total_stars": total_stars, "owned_repos": repo_count}
        except requests.RequestException as e:
            logger.error(f"Falha ao calcular estrelas: {e}")
            return {"total_stars": 0, "owned_repos": 0}

    def get_total_commits(self) -> int:
        """
        Obtém a contagem de commits realizados pelo autor.
        Utiliza o endpoint de busca de commits do GitHub.
        Caso o limite de busca seja atingido, faz fallback seguro.
        """
        search_url = f"{self.BASE_URL}/search/commits"
        params = {"q": f"author:{self.username}"}
        headers = {"Accept": "application/vnd.github.cloak-preview+json"}

        logger.info(f"Buscando contagem total de commits de @{self.username}...")

        try:
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                total_commits = data.get("total_count", 0)
                logger.info(f"Total de commits encontrados via Search API: {total_commits}")
                if total_commits > 0:
                    return total_commits
                logger.info("Search API retornou 0. Tentando contagem direta nos repositórios...")
            else:
                logger.warning(
                    f"Search API retornou status {response.status_code}. "
                    f"Mensagem: {response.text[:120]}. Iniciando fallback."
                )
        except requests.RequestException as err:
            logger.warning(f"Erro na requisição da Search API ({err}). Iniciando fallback.")

        # Fallback: somatório dos commits nos repositórios do usuário
        fallback_commits = self._fallback_commit_counter()
        return fallback_commits

    def _fallback_commit_counter(self) -> int:
        """Método de contingência para somar commits dos repositórios diretamente."""
        logger.info("Executando contagem de contingência via lista de commits dos repos...")
        repos_url = f"{self.BASE_URL}/users/{self.username}/repos"
        commits_total = 0

        try:
            res = self.session.get(repos_url, params={"per_page": 50, "type": "owner"}, timeout=10)
            if res.status_code == 200:
                repos = res.json()
                for repo in repos:
                    repo_name = repo.get("name")
                    commits_url = f"{self.BASE_URL}/repos/{self.username}/{repo_name}/commits"
                    c_res = self.session.get(commits_url, params={"author": self.username, "per_page": 100}, timeout=10)
                    if c_res.status_code == 200:
                        commits_total += len(c_res.json())
        except Exception as e:
            logger.error(f"Erro no fallback de commits: {e}")

        return commits_total


class SVGProfileGenerator:
    """Responsável por carregar o template SVG e injetar os dados dinâmicos."""

    def __init__(self, template_path: str, output_path: str):
        self.template_path = template_path
        self.output_path = output_path

    def render(self, metrics: Dict[str, str]) -> None:
        """Lê o template, substitui os placeholders e grava o SVG final."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Arquivo de template '{self.template_path}' não encontrado.")

        logger.info(f"Lendo template: '{self.template_path}'...")
        with open(self.template_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        logger.info("Injetando métricas dinâmicas nos placeholders...")
        for placeholder, value in metrics.items():
            pattern = f"{{{{{placeholder}}}}}"
            svg_content = svg_content.replace(pattern, str(value))
            logger.info(f"  -> {pattern} = {value}")

        # Salva o arquivo SVG final
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        logger.info(f"SVG animado gerado com sucesso em: '{self.output_path}'")


def format_number(num: int) -> str:
    """Formata inteiros com separador de milhar no padrão brasileiro."""
    return f"{num:,}".replace(",", ".")


def get_current_timestamp() -> str:
    """Retorna a data e hora formatadas no fuso horário de Brasília (UTC-3)."""
    br_timezone = timezone(timedelta(hours=-3))
    now = datetime.now(br_timezone)
    return now.strftime("%d/%m/%Y %H:%M BRT")


def main():
    """Fluxo principal de execução."""
    print("=" * 60)
    print("   INICIANDO GERADOR DE PERFIL DINÂMICO (SVG) - GITHUB")
    print("=" * 60)

    # Coleta credenciais e parâmetros das variáveis de ambiente
    username = os.getenv("GITHUB_USERNAME", "CaioCastilho")
    github_token = os.getenv("GITHUB_TOKEN")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(base_dir, "template.svg")
    output_file = os.path.join(base_dir, "perfil_animado.svg")

    # 1. Coleta de dados via API
    fetcher = GitHubStatsFetcher(username=username, token=github_token)
    user_info = fetcher.get_user_profile()
    stars_info = fetcher.get_stars_and_repos()
    total_commits = fetcher.get_total_commits()

    followers = user_info.get("followers", 0)
    public_repos = user_info.get("public_repos", stars_info.get("owned_repos", 0))
    total_stars = stars_info.get("total_stars", 0)
    timestamp = get_current_timestamp()

    # 2. Mapeamento de Placeholders
    metrics = {
        "TOTAL_COMMITS": format_number(total_commits),
        "STARS": format_number(total_stars),
        "FOLLOWERS": format_number(followers),
        "PUBLIC_REPOS": format_number(public_repos),
        "LAST_UPDATED": timestamp
    }

    # 3. Geração do SVG
    generator = SVGProfileGenerator(template_path=template_file, output_path=output_file)
    generator.render(metrics)

    print("=" * 60)
    print(f"[OK] PROCESSO CONCLUIDO COM SUCESSO! [@{username}]")
    print(f"  * Commits: {metrics['TOTAL_COMMITS']}")
    print(f"  * Stars: {metrics['STARS']}")
    print(f"  * Seguidores: {metrics['FOLLOWERS']}")
    print(f"  * Repositorios: {metrics['PUBLIC_REPOS']}")
    print(f"  * Atualizado em: {metrics['LAST_UPDATED']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
