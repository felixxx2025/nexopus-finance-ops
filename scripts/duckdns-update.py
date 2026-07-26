#!/usr/bin/env python3
"""
DuckDNS DDNS Update Script
Atualiza o endereço IP de um subdomínio DuckDNS via API.

Documentação: https://www.duckdns.org/spec.jsp
"""

import requests
import sys
from typing import Optional


def update_duckdns(
    subdomain: str,
    token: str,
    ip: Optional[str] = None,
    ipv6: Optional[str] = None,
    verbose: bool = False,
    clear: bool = False
) -> bool:
    """
    Atualiza o registro DNS do DuckDNS.
    
    Args:
        subdomain: Nome do subdomínio (sem .duckdns.org)
        token: Token da conta DuckDNS
        ip: Endereço IPv4 (opcional, detecta automaticamente se não fornecido)
        ipv6: Endereço IPv6 (opcional)
        verbose: Retorna informações detalhadas
        clear: Limpa os registros DNS
    
    Returns:
        True se atualização foi bem-sucedida, False caso contrário
    """
    base_url = "https://www.duckdns.org/update"
    
    params = {
        "domains": subdomain,
        "token": token,
    }
    
    if ip:
        params["ip"] = ip
    if ipv6:
        params["ipv6"] = ipv6
    if verbose:
        params["verbose"] = "true"
    if clear:
        params["clear"] = "true"
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.text.strip()
        
        if verbose:
            print(f"Resposta: {result}")
        
        if result == "OK":
            print(f"✓ DuckDNS atualizado com sucesso: {subdomain}.duckdns.org")
            return True
        elif result.startswith("OK"):
            print(f"✓ DuckDNS atualizado com sucesso: {subdomain}.duckdns.org")
            print(f"  Detalhes: {result}")
            return True
        else:
            print(f"✗ Erro ao atualizar DuckDNS: {result}")
            return False
            
    except requests.RequestException as e:
        print(f"✗ Erro de conexão com DuckDNS: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Uso: python duckdns-update.py <subdomain> <token> [ip] [ipv6]")
        print("\nExemplo:")
        print("  python duckdns-update.py nexopus-finance SEU_TOKEN")
        print("  python duckdns-update.py nexopus-finance SEU_TOKEN 192.168.1.100")
        print("  python duckdns-update.py nexopus-finance SEU_TOKEN 192.168.1.100 2001:db8::1")
        sys.exit(1)
    
    subdomain = sys.argv[1]
    token = sys.argv[2]
    ip = sys.argv[3] if len(sys.argv) > 3 else None
    ipv6 = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = update_duckdns(
        subdomain=subdomain,
        token=token,
        ip=ip,
        ipv6=ipv6,
        verbose=True
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
