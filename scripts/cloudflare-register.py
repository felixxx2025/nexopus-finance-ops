#!/usr/bin/env python3
"""
Cloudflare Registrar API Script
Registra domínios via API do Cloudflare Registrar.

Documentação: https://blog.cloudflare.com/registrar-api-beta/
API Docs: https://developers.cloudflare.com/api/resources/registrar/subresources/domains/

Requisitos:
- Conta Cloudflare com Cloudflare Registrar ativado
- API Token com permissões: Account > Registrar > Edit
- Método de pagamento configurado na conta Cloudflare
"""

import requests
import sys
import time
from typing import Optional, Dict, List


class CloudflareRegistrar:
    """Cliente para API do Cloudflare Registrar"""
    
    def __init__(self, api_token: str, account_id: str):
        """
        Inicializa cliente Cloudflare Registrar.
        
        Args:
            api_token: API Token do Cloudflare
            account_id: ID da conta Cloudflare
        """
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def search_domains(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca sugestões de domínios baseadas em uma query.
        
        Args:
            query: Termo de busca (ex: "nexopus finance")
            limit: Número máximo de resultados
            
        Returns:
            Lista de domínios sugeridos com preços
        """
        url = f"{self.base_url}/accounts/{self.account_id}/registrar/domain-search"
        params = {"q": query, "limit": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("result", {}).get("domains", [])
            else:
                print(f"✗ Erro na busca: {data.get('errors')}")
                return []
                
        except requests.RequestException as e:
            print(f"✗ Erro de conexão: {e}")
            return []
    
    def check_availability(self, domains: List[str]) -> List[Dict]:
        """
        Verifica disponibilidade e preço atual de domínios específicos.
        
        Args:
            domains: Lista de domínios para verificar (ex: ["nexopus-finance.com"])
            
        Returns:
            Lista de domínios com status de disponibilidade e preço
        """
        url = f"{self.base_url}/accounts/{self.account_id}/registrar/domain-check"
        body = {"domains": domains}
        
        try:
            response = requests.post(url, headers=self.headers, json=body, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("result", {}).get("domains", [])
            else:
                print(f"✗ Erro na verificação: {data.get('errors')}")
                return []
                
        except requests.RequestException as e:
            print(f"✗ Erro de conexão: {e}")
            return []
    
    def register_domain(self, domain_name: str) -> Dict:
        """
        Registra um domínio.
        
        Args:
            domain_name: Nome do domínio (ex: "nexopus-finance.dev")
            
        Returns:
            Resultado do registro
        """
        url = f"{self.base_url}/accounts/{self.account_id}/registrar/registrations"
        body = {"domain_name": domain_name}
        
        try:
            response = requests.post(url, headers=self.headers, json=body, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("result", {})
            else:
                print(f"✗ Erro no registro: {data.get('errors')}")
                return {}
                
        except requests.RequestException as e:
            print(f"✗ Erro de conexão: {e}")
            return {}
    
    def print_search_results(self, domains: List[Dict]):
        """Imprime resultados de busca de forma formatada"""
        if not domains:
            print("Nenhum domínio encontrado.")
            return
        
        print("\n" + "="*80)
        print("DOMÍNIOS ENCONTRADOS")
        print("="*80)
        
        for i, domain in enumerate(domains, 1):
            name = domain.get("name", "N/A")
            registrable = domain.get("registrable", False)
            tier = domain.get("tier", "standard")
            pricing = domain.get("pricing", {})
            currency = pricing.get("currency", "USD")
            reg_cost = pricing.get("registration_cost", "N/A")
            renew_cost = pricing.get("renewal_cost", "N/A")
            
            status = "✓ Disponível" if registrable else "✗ Indisponível"
            
            print(f"\n{i}. {name}")
            print(f"   Status: {status}")
            print(f"   Tipo: {tier}")
            print(f"   Registro: {currency} ${reg_cost}")
            print(f"   Renovação: {currency} ${renew_cost}")
    
    def print_availability_results(self, domains: List[Dict]):
        """Imprime resultados de verificação de disponibilidade"""
        if not domains:
            print("Nenhum resultado.")
            return
        
        print("\n" + "="*80)
        print("DISPONIBILIDADE ATUAL")
        print("="*80)
        
        for domain in domains:
            name = domain.get("name", "N/A")
            registrable = domain.get("registrable", False)
            pricing = domain.get("pricing", {})
            currency = pricing.get("currency", "USD")
            reg_cost = pricing.get("registration_cost", "N/A")
            
            status = "✓ Disponível" if registrable else "✗ Indisponível"
            
            print(f"\n{name}")
            print(f"   Status: {status}")
            print(f"   Preço: {currency} ${reg_cost}")


def main():
    if len(sys.argv) < 4:
        print("Uso: python cloudflare-register.py <api_token> <account_id> <comando> [args]")
        print("\nComandos:")
        print("  search <query>        - Busca sugestões de domínios")
        print("  check <domain>        - Verifica disponibilidade de um domínio")
        print("  register <domain>    - Registra um domínio")
        print("\nExemplos:")
        print("  python cloudflare-register.py TOKEN ACCOUNT search 'nexopus finance'")
        print("  python cloudflare-register.py TOKEN ACCOUNT check nexopus-finance.dev")
        print("  python cloudflare-register.py TOKEN ACCOUNT register nexopus-finance.dev")
        sys.exit(1)
    
    api_token = sys.argv[1]
    account_id = sys.argv[2]
    command = sys.argv[3]
    
    registrar = CloudflareRegistrar(api_token, account_id)
    
    if command == "search":
        if len(sys.argv) < 5:
            print("Erro: query necessária para busca")
            sys.exit(1)
        
        query = sys.argv[4]
        print(f"Buscando domínios para: {query}")
        domains = registrar.search_domains(query)
        registrar.print_search_results(domains)
    
    elif command == "check":
        if len(sys.argv) < 5:
            print("Erro: domínio necessário para verificação")
            sys.exit(1)
        
        domain = sys.argv[4]
        print(f"Verificando disponibilidade: {domain}")
        domains = registrar.check_availability([domain])
        registrar.print_availability_results(domains)
    
    elif command == "register":
        if len(sys.argv) < 5:
            print("Erro: domínio necessário para registro")
            sys.exit(1)
        
        domain = sys.argv[4]
        
        # Primeiro verificar disponibilidade
        print(f"Verificando disponibilidade: {domain}")
        availability = registrar.check_availability([domain])
        
        if not availability or not availability[0].get("registrable"):
            print(f"✗ Domínio {domain} não está disponível para registro")
            sys.exit(1)
        
        # Mostrar preço
        pricing = availability[0].get("pricing", {})
        currency = pricing.get("currency", "USD")
        cost = pricing.get("registration_cost", "N/A")
        print(f"\nPreço de registro: {currency} ${cost}")
        
        # Confirmar
        confirm = input(f"\nConfirmar registro de {domain}? (s/n): ")
        if confirm.lower() != 's':
            print("Registro cancelado.")
            sys.exit(0)
        
        # Registrar
        print(f"\nRegistrando {domain}...")
        result = registrar.register_domain(domain)
        
        if result:
            state = result.get("state", "unknown")
            completed = result.get("completed", False)
            
            if state == "succeeded" and completed:
                print(f"✓ Domínio {domain} registrado com sucesso!")
                
                # Mostrar detalhes
                context = result.get("context", {}).get("registration", {})
                expires_at = context.get("expires_at", "N/A")
                auto_renew = context.get("auto_renew", False)
                privacy = context.get("privacy_enabled", False)
                
                print(f"\nDetalhes:")
                print(f"  Expira em: {expires_at}")
                print(f"  Auto-renovação: {'Sim' if auto_renew else 'Não'}")
                print(f"  Privacidade WHOIS: {'Ativada' if privacy else 'Desativada'}")
            else:
                print(f"⚠ Registro em processamento. Estado: {state}")
        else:
            print(f"✗ Falha ao registrar domínio")
            sys.exit(1)
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
