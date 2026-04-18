import os
import datetime
import json
import yaml
import toml
import configparser
import shutil
import io

class ConfigParseError(Exception):
    """Custom exception for configuration parsing errors with line/column info."""
    def __init__(self, message, line=None, col=None):
        super().__init__(message)
        self.line = line
        self.col = col

def read_config(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif ext in ['.yaml', '.yml']:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        elif ext in ['.ini', '.cfg', '.conf']:
            parser = configparser.ConfigParser()
            parser.optionxform = str
            parser.read(path, encoding='utf-8')
            res = {}
            if parser.defaults():
                res['DEFAULT'] = dict(parser.defaults())
            for section in parser.sections():
                res[section] = dict(parser.items(section))
            return res
        elif ext == '.toml':
            with open(path, 'r', encoding='utf-8') as f:
                return toml.load(f)
        else:
            raise ValueError(f"サポートされていない形式です: {ext}")
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"JSON解釈エラー: {e.msg}", e.lineno, e.colno)
    except toml.TomlDecodeError as e:
        raise ConfigParseError(f"TOML解釈エラー: {str(e)}")
    except yaml.YAMLError as e:
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            raise ConfigParseError(f"YAML解釈エラー: {e.problem}", mark.line + 1, mark.column + 1)
        raise ConfigParseError(f"YAML解釈エラー: {str(e)}")
    except configparser.Error as e:
        raise ConfigParseError(f"INI形式エラー: {str(e)}")
    except Exception as e:
        raise Exception(f"ファイルの読み込みに失敗しました ({path}):\n{e}")

def save_config(path: str, data: dict):
    ext = os.path.splitext(path)[1].lower()
    try:
        # 履歴管理 (History Management)
        if os.path.exists(path):
            history_dir = os.path.join(os.path.dirname(path), ".dotvis_history")
            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = os.path.basename(path)
            backup_path = os.path.join(history_dir, f"{basename}.{timestamp}.bak")
            shutil.copy2(path, backup_path)
            
            # 最大10世代まで保持 (Keep up to 10 versions)
            all_backups = sorted([os.path.join(history_dir, f) for f in os.listdir(history_dir) if f.startswith(basename)], 
                               key=os.path.getmtime, reverse=True)
            if len(all_backups) > 10:
                for old in all_backups[10:]:
                    try:
                        os.remove(old)
                    except OSError:
                        pass

        if ext == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif ext in ['.yaml', '.yml']:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        elif ext in ['.ini', '.cfg', '.conf']:
            parser = configparser.ConfigParser()
            parser.optionxform = str
            for section, items in data.items():
                if isinstance(items, dict):
                    if section == 'DEFAULT':
                        for k, v in items.items():
                            parser.set(configparser.DEFAULTSECT, k, str(v))
                    else:
                        parser[section] = {k: str(v) for k, v in items.items()}
                else:
                    parser.set(configparser.DEFAULTSECT, str(section), str(items))
            with open(path, 'w', encoding='utf-8') as f:
                parser.write(f)
        elif ext == '.toml':
            with open(path, 'w', encoding='utf-8') as f:
                toml.dump(data, f)
        else:
            raise ValueError(f"サポートされていない形式です: {ext}")
    except Exception as e:
        raise Exception(f"保存に失敗しました ({path}):\n{e}")
