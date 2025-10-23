# Teste do script original com timeout
import subprocess
import time
import signal
import os

def test_original_script():
    """Testa o script original por alguns segundos."""
    print("Testando o script original por 30 segundos...")
    
    try:
        # Inicia o processo
        process = subprocess.Popen(
            ["python", "teste02/portfoliolib_project/examples/run_live_equal_weight_volatility.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Lê a saída por 30 segundos
        start_time = time.time()
        output_lines = []
        
        while time.time() - start_time < 30:
            # Lê uma linha se disponível
            if process.poll() is None:
                try:
                    line = process.stdout.readline()
                    if line:
                        print(line.strip())
                        output_lines.append(line.strip())
                except:
                    pass
            else:
                # Processo terminou
                break
            
            time.sleep(0.1)
        
        # Termina o processo se ainda estiver rodando
        if process.poll() is None:
            print("\nTerminando processo após 30 segundos...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print(f"\nTeste concluído. Total de linhas capturadas: {len(output_lines)}")
        
        # Verifica se conseguiu conectar e iniciar
        output_text = "\n".join(output_lines)
        if "Conectado ao MetaTrader 5" in output_text:
            print("✅ SUCESSO: Conectou ao MetaTrader 5")
        else:
            print("❌ FALHA: Não conseguiu conectar ao MetaTrader 5")
            
        if "INICIANDO TRADING AO VIVO" in output_text:
            print("✅ SUCESSO: Iniciou o trading ao vivo")
        else:
            print("❌ FALHA: Não chegou ao trading ao vivo")
            
        if "PortfolioAgent INICIADO" in output_text:
            print("✅ SUCESSO: PortfolioAgent foi iniciado")
        else:
            print("❌ FALHA: PortfolioAgent não foi iniciado")
            
    except Exception as e:
        print(f"Erro durante o teste: {e}")

if __name__ == "__main__":
    test_original_script()

