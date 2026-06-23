import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


class PresenceAgentAdminMenu:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.app_dir = self.project_root / "app"
        self.data_dir = self.app_dir / "data"
        self.faces_dir = self.data_dir / "faces"
        self.models_dir = self.data_dir / "models"
        self.runtime_dir = self.data_dir / "runtime"
        self.logs_dir = self.project_root / "logs"
        self.config_dir = self.app_dir / "config"
        self.startup_apps_path = self.config_dir / "startup_apps.json"
        self.env_path = self.project_root / ".env"

        self.assets_dir = self.project_root / "assets"
        self.logo_path = self.assets_dir / "mcom_ascii.txt"
        
    def run(self):
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            option = input("\nEscolha uma opção: ").strip()

            if option == "1":
                self.show_status()
            elif option == "2":
                self.enroll_user()
            elif option == "3":
                self.train_recognizer()
            elif option == "4":
                self.test_recognizer()
            elif option == "5":
                self.validate_startup_apps()
            elif option == "6":
                self.open_logs_folder()
            elif option == "7":
                self.open_latest_log()
            elif option == "8":
                self.stop_running_agent()
            elif option == "9":
                self.remove_user_face_samples()
            elif option == "10":
                self.purge_biometric_data()
            elif option == "11":
                self.lgpd_readiness_report()
            elif option == "0":
                print("\nSaindo do menu administrativo.")
                break
            else:
                print("\nOpção inválida.")
                self.pause()

    def enable_ansi_colors(self):
        # Ajuda o terminal do Windows a aceitar cores ANSI.
        os.system("")

    def color(self, text, ansi_code):
        return f"\033[{ansi_code}m{text}\033[0m"

    def load_logo(self):
        if not self.logo_path.exists():
            return None

        logo = self.logo_path.read_text(encoding="utf-8")

        # Caso a arte venha com \# por causa de escape/cópia.
        logo = logo.replace("\\#", "#")

        return logo.rstrip()

    def print_header(self):
        self.enable_ansi_colors()

        logo = self.load_logo()

        if logo:
            print(self.color(logo, "36"))

        print(self.color("=" * 72, "36"))
        print(self.color("MCOM | PresenceAgent - Console Administrativo", "1;37"))
        print(self.color("=" * 72, "36"))
        print(self.color("Uso restrito: TI / suporte autorizado", "33"))
        print(self.color("Atenção: este menu manipula dados biométricos locais.", "31"))
        print(self.color("=" * 72, "36"))

    def print_menu(self):
        print()
        print(self.color("OPERAÇÃO", "1;36"))
        print("  [1] Ver status do ambiente")
        print("  [2] Cadastrar / atualizar rosto do usuário")
        print("  [3] Treinar modelo facial")
        print("  [4] Testar reconhecedor facial")
        print("  [5] Validar startup_apps.json")
        print("  [6] Abrir pasta de logs")
        print("  [7] Abrir log mais recente")
        print("  [8] Encerrar PresenceAgent em execução")

        print()
        print(self.color("DADOS BIOMÉTRICOS", "1;35"))
        print("  [9] Remover amostras faciais de um usuário")
        print(" [10] Apagar TODOS os dados biométricos locais")

        print()
        print(self.color("GOVERNANÇA / LGPD", "1;33"))
        print(" [11] Exibir relatório de prontidão LGPD")

        print()
        print(self.color("SAIR", "1;37"))
        print("  [0] Sair")

    def show_status(self):
        self.clear_screen()
        self.print_section("Status do ambiente")

        print(f"Projeto: {self.project_root}")
        print(f"Python: {sys.executable}")
        print(f".env existe: {self.exists_text(self.env_path)}")
        print(f"startup_apps.json existe: {self.exists_text(self.startup_apps_path)}")
        print(f"faces dir existe: {self.exists_text(self.faces_dir)}")
        print(f"models dir existe: {self.exists_text(self.models_dir)}")
        print(f"logs dir existe: {self.exists_text(self.logs_dir)}")

        print("\nUsuários com amostras faciais:")
        users = self.list_face_users()
        if not users:
            print("  Nenhum usuário cadastrado em app/data/faces.")
        else:
            for user in users:
                sample_count = len(list((self.faces_dir / user).glob("*.jpg")))
                print(f"  - {user}: {sample_count} amostras .jpg")

        print("\nModelos:")
        model_files = list(self.models_dir.glob("*")) if self.models_dir.exists() else []
        if not model_files:
            print("  Nenhum arquivo de modelo encontrado.")
        else:
            for file in model_files:
                print(f"  - {file.name} ({file.stat().st_size} bytes)")

        print("\nLogs recentes:")
        for log in self.get_recent_logs(limit=5):
            print(f"  - {log.name} ({log.stat().st_size} bytes)")

        self.pause()

    def enroll_user(self):
        self.clear_screen()
        self.print_section("Cadastrar / atualizar rosto")

        user = input("Identificador do usuário autorizado, ex: login institucional: ").strip()
        if not user:
            print("Usuário não informado.")
            self.pause()
            return

        samples = input("Quantidade de amostras [300]: ").strip() or "300"

        if not samples.isdigit():
            print("Quantidade inválida.")
            self.pause()
            return

        print("\nOrientações:")
        print("- Capture frente, meio de lado, esquerda, direita e iluminação real.")
        print("- Evite imagens borradas, muito escuras ou com rosto muito cortado.")
        print("- Dados capturados são biométricos e devem ser tratados como sensíveis.")

        if not self.confirm("Iniciar captura facial agora?"):
            return

        self.run_python_tool("tools/enroll_user.py", ["--user", user, "--samples", samples])
        if self.confirm(f"Deseja definir AUTHORIZED_USER={user} no .env?"):
            self.update_env_value("AUTHORIZED_USER", user)
            print(f"AUTHORIZED_USER atualizado para: {user}")
        self.pause()

    def update_env_value(self, key, value):
        lines = []

        if self.env_path.exists():
            lines = self.env_path.read_text(encoding="utf-8").splitlines()

        updated = False
        new_lines = []

        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"{key}={value}")

        self.env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def train_recognizer(self):
        self.clear_screen()
        self.print_section("Treinar modelo facial")

        print("Este processo lê app/data/faces e gera/atualiza app/data/models.")
        print("Em uso institucional, as imagens brutas devem ser apagadas após validação do modelo.")
        print("O modelo treinado continua sendo dado biométrico sensível e deve ser protegido.")

        if not self.confirm("Treinar modelo agora?"):
            return

        success = self.run_python_tool("tools/train_recognizer.py", [])

        if not success:
            print("\nTreinamento não concluído. Verifique os erros acima.")
            self.pause()
            return

        print("\nTreinamento concluído.")
        print("Por segurança/LGPD, recomenda-se apagar as imagens faciais brutas após validar o modelo.")
        print("Atenção: se apagar as imagens, para retreinar será necessário coletar novas amostras.")

        if self.confirm("Deseja apagar agora as imagens faciais brutas de treinamento?"):
            self.remove_all_face_samples_after_training()

        self.pause()
    
    def remove_all_face_samples_after_training(self):
        if not self.faces_dir.exists():
            print("Pasta de amostras faciais não encontrada.")
            return

        users = self.list_face_users()

        if not users:
            print("Nenhuma amostra facial encontrada para remoção.")
            return

        print("\nUsuários com amostras faciais:")
        for user in users:
            user_dir = self.faces_dir / user
            sample_count = len(list(user_dir.glob("*.jpg")))
            print(f"  - {user}: {sample_count} imagens")

        print("\nATENÇÃO: esta ação remove as imagens brutas, mas mantém o modelo treinado.")
        print("Após remover, para retreinar será necessário capturar novas imagens.")

        if not self.confirm_typed("APAGAR AMOSTRAS"):
            return

        for user in users:
            user_dir = self.faces_dir / user
            if user_dir.exists():
                shutil.rmtree(user_dir)

        self.faces_dir.mkdir(parents=True, exist_ok=True)

        print("Amostras faciais brutas apagadas com sucesso.")

    def test_recognizer(self):
        self.clear_screen()
        self.print_section("Testar reconhecedor facial")

        print("Use este teste para validar faixas de confiança antes de habilitar lock automático.")
        print("Referência atual sugerida:")
        print("  <= 55  autorizado")
        print("  56-64  incerto")
        print("  >= 65  desconhecido")

        if not self.confirm("Iniciar teste do reconhecedor?"):
            return

        self.run_python_tool("tools/test_recognizer.py", [])
        self.pause()

    def validate_startup_apps(self):
        self.clear_screen()
        self.print_section("Validar startup_apps.json")

        if not self.startup_apps_path.exists():
            print(f"Arquivo não encontrado: {self.startup_apps_path}")
            self.pause()
            return

        try:
            data = json.loads(self.startup_apps_path.read_text(encoding="utf-8"))
        except Exception as error:
            print(f"JSON inválido: {error}")
            self.pause()
            return

        if not isinstance(data, list):
            print("Formato inválido: o JSON deve ser uma lista.")
            self.pause()
            return

        print("Arquivo JSON válido. Itens encontrados:\n")
        for index, app in enumerate(data, start=1):
            name = app.get("name", "sem nome")
            enabled = app.get("enabled", True)
            app_type = app.get("type", "process")
            target = app.get("target", "")
            args = app.get("args", [])

            print(f"{index}. {name}")
            print(f"   enabled: {enabled}")
            print(f"   type: {app_type}")
            print(f"   target: {target}")
            print(f"   args: {args}")

            if app_type == "process" and target:
                target_path = Path(target)
                if "\\" in target or "/" in target:
                    print(f"   executável existe: {target_path.exists()}")

            print()

        self.pause()

    def open_logs_folder(self):
        self.logs_dir.mkdir(exist_ok=True)
        os.startfile(self.logs_dir)
        self.pause("Pasta de logs aberta. Pressione ENTER para continuar...")

    def open_latest_log(self):
        logs = self.get_recent_logs(limit=1)
        if not logs:
            print("Nenhum log encontrado.")
            self.pause()
            return

        os.startfile(logs[0])
        self.pause("Log mais recente aberto. Pressione ENTER para continuar...")

    
    def stop_running_agent(self):
        self.clear_screen()
        self.print_section("Encerrar PresenceAgent")

        print(
            "Este comando encerra processos python.exe/pythonw.exe "
            "que estejam executando main.py deste projeto."
        )

        if not self.confirm("Encerrar PresenceAgent em execução?"):
            return

        project_name = self.project_root.name

        command = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { "
            "($_.Name -eq 'pythonw.exe' -or $_.Name -eq 'python.exe') "
            f"-and $_.CommandLine -like '*{project_name}*main.py*' "
            "} | "
            "ForEach-Object { "
            "Stop-Process -Id $_.ProcessId -Force; "
            "Write-Host \"PresenceAgent encerrado: $($_.ProcessId)\" "
            "}"
        )


        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            cwd=self.project_root,
        )

        self.pause()

    def remove_user_face_samples(self):
        self.clear_screen()
        self.print_section("Remover amostras faciais de usuário")

        users = self.list_face_users()
        if not users:
            print("Nenhum usuário com amostras encontrado.")
            self.pause()
            return

        print("Usuários encontrados:")
        for user in users:
            print(f"  - {user}")

        user = input("\nUsuário para remover amostras: ").strip()
        user_dir = self.faces_dir / user

        if not user_dir.exists():
            print("Usuário não encontrado.")
            self.pause()
            return

        print("\nATENÇÃO: isto remove imagens faciais brutas usadas para treinamento.")
        print("O modelo treinado em app/data/models não será apagado por esta opção.")

        if not self.confirm_typed(f"REMOVER {user}"):
            return

        shutil.rmtree(user_dir)
        print(f"Amostras removidas: {user_dir}")
        self.pause()

    def purge_biometric_data(self):
        self.clear_screen()
        self.print_section("Apagar TODOS os dados biométricos locais")

        print("ATENÇÃO: esta ação remove:")
        print(f"- {self.faces_dir}")
        print(f"- {self.models_dir}")
        print("\nIsso apaga amostras faciais e modelos treinados locais.")
        print("Use somente em procedimento de desativação, troca de PC ou incidente.")

        if not self.confirm_typed("APAGAR DADOS BIOMETRICOS"):
            return

        if self.faces_dir.exists():
            shutil.rmtree(self.faces_dir)
        if self.models_dir.exists():
            shutil.rmtree(self.models_dir)

        self.faces_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        print("Dados biométricos locais apagados.")
        self.pause()

    def lgpd_readiness_report(self):
        self.clear_screen()
        self.print_section("Relatório de prontidão LGPD")

        print("Resumo técnico atual:\n")
        print("1. Dados tratados")
        print("   - Imagens faciais de treinamento em app/data/faces.")
        print("   - Modelo biométrico treinado em app/data/models.")
        print("   - Logs operacionais em logs/.")

        print("\n2. Classificação")
        print("   - Dados biométricos vinculados a pessoa natural devem ser tratados como dados pessoais sensíveis.")

        print("\n3. Estado atual")
        print("   - Processamento local.")
        print("   - Sem envio para nuvem por padrão.")
        print("   - Imagens brutas ainda podem existir após cadastro.")
        print("   - Modelo ainda não está criptografado pela aplicação.")
        print("   - Controle de acesso depende das permissões do sistema de arquivos atual.")

        print("\n4. Recomendações para uso institucional")
        print("   - Mover dados para C:\\ProgramData\\PresenceAgent.")
        print("   - Aplicar ACL restrita para TI/Administradores/SYSTEM.")
        print("   - Apagar imagens brutas após treino validado.")
        print("   - Criptografar modelo biométrico em repouso.")
        print("   - Criar procedimento de recadastro, exclusão, troca de PC e incidente.")
        print("   - Separar logs operacionais de logs sensíveis.")
        print("   - Definir retenção de logs.")
        print("   - Validar finalidade, base legal e governança com Encarregado/DPO.")

        print("\n5. Próximas evoluções técnicas preparadas")
        print("   - Menu administrativo centralizado.")
        print("   - Rotina de limpeza de biometria.")
        print("   - Pontos futuros para criptografia e ProgramData.")
        print("   - Base para documentação institucional.")

        self.pause()

    def run_python_tool(self, relative_path, args):
        tool_path = self.project_root / relative_path

        if not tool_path.exists():
            print(f"Ferramenta não encontrada: {tool_path}")
            return False

        command = [sys.executable, str(tool_path)] + args

        print("\nExecutando:")
        print(" ".join(command))
        print()

        result = subprocess.run(command, cwd=self.project_root)

        if result.returncode != 0:
            print(f"\nFerramenta terminou com erro. Código: {result.returncode}")
            return False

        return True

    def list_face_users(self):
        if not self.faces_dir.exists():
            return []

        return sorted(
            path.name for path in self.faces_dir.iterdir()
            if path.is_dir()
        )

    def get_recent_logs(self, limit=5):
        if not self.logs_dir.exists():
            return []

        logs = [path for path in self.logs_dir.glob("*.log") if path.is_file()]
        return sorted(logs, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]

    def exists_text(self, path):
        return "sim" if path.exists() else "não"

    def confirm(self, message):
        answer = input(f"{message} [s/N]: ").strip().lower()
        return answer == "s"

    def confirm_typed(self, expected_text):
        print(f"\nPara confirmar, digite exatamente: {expected_text}")
        answer = input("> ").strip()
        if answer != expected_text:
            print("Confirmação inválida. Ação cancelada.")
            self.pause()
            return False
        return True

    def print_section(self, title):
        print("=" * 72)
        print(title)
        print("=" * 72)

    def pause(self, message="Pressione ENTER para continuar..."):
        input(f"\n{message}")

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")


if __name__ == "__main__":
    menu = PresenceAgentAdminMenu()
    menu.run()