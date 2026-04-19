"""
Módulo de banco de dados SQLite para o LaBlu System.
"""

import sqlite3
import shutil
from pathlib import Path


class Database:
    def __init__(self):
        base_dir = Path(__file__).parent
        self.db_path = base_dir / "data" / "lablu.db"
        self.images_dir = base_dir / "images"
        self.db_path.parent.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                ordem INTEGER DEFAULT 0,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS filamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                marca TEXT,
                cor TEXT,
                diametro TEXT DEFAULT '1.75mm',
                temperatura_bico TEXT,
                temperatura_cama TEXT,
                peso_total TEXT,
                peso_restante TEXT,
                notas TEXT,
                imagem_path TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );

            CREATE TABLE IF NOT EXISTS categorias_impressoras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                ordem INTEGER DEFAULT 0,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS impressoras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria_id INTEGER NOT NULL,
                modelo TEXT NOT NULL,
                marca TEXT DEFAULT '',
                sku TEXT DEFAULT '',
                preco TEXT DEFAULT '',
                imagem_path TEXT DEFAULT '',
                em_estoque INTEGER DEFAULT 1,
                quantidade TEXT DEFAULT '',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias_impressoras(id)
            );
        """)

        # Migrações de colunas
        colunas = [row[1] for row in cursor.execute("PRAGMA table_info(filamentos)").fetchall()]
        if "sku" not in colunas:
            cursor.execute("ALTER TABLE filamentos ADD COLUMN sku TEXT DEFAULT ''")
        if "em_estoque" not in colunas:
            cursor.execute("ALTER TABLE filamentos ADD COLUMN em_estoque INTEGER DEFAULT 1")
        if "quantidade" not in colunas:
            cursor.execute("ALTER TABLE filamentos ADD COLUMN quantidade TEXT DEFAULT ''")

        # Migração: apaga registros com soft delete e remove coluna ativo
        self._migrate_remove_soft_delete(cursor)

        # Índices para buscas rápidas por categoria e nome
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filamentos_categoria ON filamentos(categoria_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filamentos_nome ON filamentos(nome)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impressoras_categoria ON impressoras(categoria_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impressoras_modelo ON impressoras(modelo)")

        conn.commit()
        conn.close()

    def _migrate_remove_soft_delete(self, cursor):
        """Remove registros com ativo=0 e dropa a coluna ativo das duas tabelas."""
        # Filamentos inativos — apaga imagens antes
        colunas_fil = [row[1] for row in cursor.execute("PRAGMA table_info(filamentos)").fetchall()]
        if "ativo" in colunas_fil:
            rows = cursor.execute(
                "SELECT imagem_path FROM filamentos WHERE ativo = 0"
            ).fetchall()
            for row in rows:
                img = row[0]
                if img:
                    p = Path(img)
                    if p.exists():
                        p.unlink(missing_ok=True)
            cursor.execute("DELETE FROM filamentos WHERE ativo = 0")
            cursor.execute("DROP INDEX IF EXISTS idx_filamentos_ativo")
            cursor.execute("ALTER TABLE filamentos DROP COLUMN ativo")

        # Impressoras inativas
        colunas_imp = [row[1] for row in cursor.execute("PRAGMA table_info(impressoras)").fetchall()]
        if "ativo" in colunas_imp:
            rows = cursor.execute(
                "SELECT imagem_path FROM impressoras WHERE ativo = 0"
            ).fetchall()
            for row in rows:
                img = row[0]
                if img:
                    p = Path(img)
                    if p.exists():
                        p.unlink(missing_ok=True)
            cursor.execute("DELETE FROM impressoras WHERE ativo = 0")
            cursor.execute("DROP INDEX IF EXISTS idx_impressoras_ativo")
            cursor.execute("ALTER TABLE impressoras DROP COLUMN ativo")

    # ─── CATEGORIAS ───────────────────────────────────────────────────────────

    def get_categorias(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM categorias ORDER BY ordem, nome").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_categoria(self, nome):
        conn = self.get_connection()
        try:
            conn.execute("INSERT INTO categorias (nome) VALUES (?)", (nome.strip(),))
            conn.commit()
            return True, "Categoria adicionada com sucesso."
        except sqlite3.IntegrityError:
            return False, "Já existe uma categoria com esse nome."
        finally:
            conn.close()

    def update_categoria(self, categoria_id, nome):
        conn = self.get_connection()
        try:
            conn.execute("UPDATE categorias SET nome = ? WHERE id = ?", (nome.strip(), categoria_id))
            conn.commit()
            return True, "Categoria atualizada."
        except sqlite3.IntegrityError:
            return False, "Já existe uma categoria com esse nome."
        finally:
            conn.close()

    def delete_categoria(self, categoria_id):
        conn = self.get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM filamentos WHERE categoria_id = ?",
            (categoria_id,)
        ).fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"Não é possível excluir: há {count} filamento(s) nesta categoria."
        conn.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        conn.commit()
        conn.close()
        return True, "Categoria excluída."

    def reorder_categorias(self, ids_ordered):
        conn = self.get_connection()
        for ordem, cat_id in enumerate(ids_ordered):
            conn.execute("UPDATE categorias SET ordem = ? WHERE id = ?", (ordem, cat_id))
        conn.commit()
        conn.close()

    # ─── FILAMENTOS ───────────────────────────────────────────────────────────

    def get_filamentos(self, categoria_id=None, apenas_em_estoque=False):
        conn = self.get_connection()
        query = """
            SELECT f.*, c.nome as categoria_nome
            FROM filamentos f
            JOIN categorias c ON f.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        if categoria_id is not None:
            query += " AND f.categoria_id = ?"
            params.append(categoria_id)
        if apenas_em_estoque:
            query += " AND f.em_estoque = 1"
        query += " ORDER BY c.nome, f.nome"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_filamento(self, filamento_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM filamentos WHERE id = ?", (filamento_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_filamento(self, dados):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO filamentos
                (categoria_id, nome, marca, cor, diametro, temperatura_bico,
                 temperatura_cama, peso_total, peso_restante, notas, imagem_path, sku, em_estoque, quantidade)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            dados.get("categoria_id"),
            dados.get("nome", "").strip(),
            dados.get("marca", "").strip(),
            dados.get("cor", "").strip(),
            dados.get("diametro", "1.75mm").strip(),
            dados.get("temperatura_bico", "").strip(),
            dados.get("temperatura_cama", "").strip(),
            dados.get("peso_total", "").strip(),
            dados.get("peso_restante", "").strip(),
            dados.get("notas", "").strip(),
            dados.get("imagem_path", ""),
            dados.get("sku", "").strip(),
            1 if dados.get("em_estoque", True) else 0,
            dados.get("quantidade", "").strip(),
        ))
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return new_id

    def update_filamento(self, filamento_id, dados):
        conn = self.get_connection()
        conn.execute("""
            UPDATE filamentos SET
                categoria_id=?, nome=?, marca=?, cor=?, diametro=?,
                temperatura_bico=?, temperatura_cama=?, peso_total=?,
                peso_restante=?, notas=?, imagem_path=?, sku=?, em_estoque=?, quantidade=?,
                atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            dados.get("categoria_id"),
            dados.get("nome", "").strip(),
            dados.get("marca", "").strip(),
            dados.get("cor", "").strip(),
            dados.get("diametro", "1.75mm").strip(),
            dados.get("temperatura_bico", "").strip(),
            dados.get("temperatura_cama", "").strip(),
            dados.get("peso_total", "").strip(),
            dados.get("peso_restante", "").strip(),
            dados.get("notas", "").strip(),
            dados.get("imagem_path", ""),
            dados.get("sku", "").strip(),
            1 if dados.get("em_estoque", True) else 0,
            dados.get("quantidade", "").strip(),
            filamento_id,
        ))
        conn.commit()
        conn.close()

    def bulk_patch_filamentos(self, ids: list, campos: dict):
        """Atualiza apenas os campos fornecidos em múltiplos filamentos."""
        if not ids or not campos:
            return
        allowed = {"categoria_id", "peso_total", "quantidade"}
        sets = [f"{k} = ?" for k in campos if k in allowed]
        vals = [v for k, v in campos.items() if k in allowed]
        if not sets:
            return
        conn = self.get_connection()
        placeholders = ",".join("?" * len(ids))
        conn.execute(
            f"UPDATE filamentos SET {', '.join(sets)}, atualizado_em=CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            vals + ids
        )
        conn.commit()
        conn.close()

    def bulk_patch_impressoras(self, ids: list, campos: dict):
        """Atualiza apenas os campos fornecidos em múltiplas impressoras."""
        if not ids or not campos:
            return
        allowed = {"categoria_id", "preco", "quantidade"}
        sets = [f"{k} = ?" for k in campos if k in allowed]
        vals = [v for k, v in campos.items() if k in allowed]
        if not sets:
            return
        conn = self.get_connection()
        placeholders = ",".join("?" * len(ids))
        conn.execute(
            f"UPDATE impressoras SET {', '.join(sets)}, atualizado_em=CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            vals + ids
        )
        conn.commit()
        conn.close()

    def set_estoque(self, filamento_id, em_estoque: bool):
        """Atualiza só o campo estoque — chamado direto pelo checkbox do card."""
        conn = self.get_connection()
        conn.execute(
            "UPDATE filamentos SET em_estoque = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if em_estoque else 0, filamento_id)
        )
        conn.commit()
        conn.close()

    def delete_filamento(self, filamento_id):
        conn = self.get_connection()
        row = conn.execute("SELECT imagem_path FROM filamentos WHERE id = ?", (filamento_id,)).fetchone()
        if row and row[0]:
            p = Path(row[0])
            p.unlink(missing_ok=True)
        conn.execute("DELETE FROM filamentos WHERE id = ?", (filamento_id,))
        conn.commit()
        conn.close()

    def save_image(self, source_path, filamento_id):
        dest_path = self.images_dir / f"filamento_{filamento_id}.jpg"
        try:
            from PIL import Image
            img = Image.open(source_path)
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.thumbnail((400, 400), Image.LANCZOS)
            img.save(str(dest_path), "JPEG", quality=82, optimize=True)
        except Exception:
            ext = Path(source_path).suffix.lower()
            dest_path = self.images_dir / f"filamento_{filamento_id}{ext}"
            shutil.copy2(source_path, dest_path)
        return str(dest_path)

    def duplicate_filamento(self, filamento_id, categoria_id=None, preco=None):
        """Duplica um filamento (incluindo imagem) e retorna o novo ID."""
        fil = self.get_filamento(filamento_id)
        if not fil:
            return None
        dados = dict(fil)
        dados["nome"] = fil["nome"]
        dados["imagem_path"] = ""
        for col in ("id", "criado_em", "atualizado_em"):
            dados.pop(col, None)
        if categoria_id is not None:
            dados["categoria_id"] = categoria_id
        if preco is not None:
            dados["peso_total"] = preco
        new_id = self.add_filamento(dados)
        old_img = fil.get("imagem_path", "")
        if old_img and Path(old_img).exists():
            ext = Path(old_img).suffix
            new_img = self.images_dir / f"filamento_{new_id}{ext}"
            shutil.copy2(old_img, str(new_img))
            conn = self.get_connection()
            conn.execute("UPDATE filamentos SET imagem_path = ? WHERE id = ?", (str(new_img), new_id))
            conn.commit()
            conn.close()
        return new_id

    def compress_existing_images(self):
        """Comprime imagens existentes maiores que 150 KB para JPEG 400x400."""
        try:
            from PIL import Image
        except ImportError:
            return

        LIMIT = 150 * 1024  # 150 KB
        exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

        for img_file in list(self.images_dir.iterdir()):
            if img_file.suffix.lower() not in exts:
                continue
            if img_file.stat().st_size <= LIMIT:
                continue
            try:
                img = Image.open(img_file)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.thumbnail((400, 400), Image.LANCZOS)
                new_path = img_file.with_suffix(".jpg")
                img.save(str(new_path), "JPEG", quality=82, optimize=True)
                if new_path != img_file:
                    img_file.unlink()
                    conn = self.get_connection()
                    conn.execute(
                        "UPDATE filamentos SET imagem_path = ? WHERE imagem_path = ?",
                        (str(new_path), str(img_file))
                    )
                    conn.commit()
                    conn.close()
            except Exception:
                pass

    def get_image_path(self, relative_or_abs):
        if not relative_or_abs:
            return None
        p = Path(relative_or_abs)
        return str(p) if p.exists() else None

    # ─── CATEGORIAS IMPRESSORAS ───────────────────────────────────────────────

    def get_categorias_impressoras(self):
        conn = self.get_connection()
        rows = conn.execute("SELECT * FROM categorias_impressoras ORDER BY ordem, nome").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_categoria_impressora(self, nome):
        conn = self.get_connection()
        try:
            conn.execute("INSERT INTO categorias_impressoras (nome) VALUES (?)", (nome.strip(),))
            conn.commit()
            return True, "Categoria adicionada com sucesso."
        except sqlite3.IntegrityError:
            return False, "Já existe uma categoria com esse nome."
        finally:
            conn.close()

    def update_categoria_impressora(self, categoria_id, nome):
        conn = self.get_connection()
        try:
            conn.execute("UPDATE categorias_impressoras SET nome = ? WHERE id = ?", (nome.strip(), categoria_id))
            conn.commit()
            return True, "Categoria atualizada."
        except sqlite3.IntegrityError:
            return False, "Já existe uma categoria com esse nome."
        finally:
            conn.close()

    def delete_categoria_impressora(self, categoria_id):
        conn = self.get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM impressoras WHERE categoria_id = ?",
            (categoria_id,)
        ).fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"Não é possível excluir: há {count} impressora(s) nesta categoria."
        conn.execute("DELETE FROM categorias_impressoras WHERE id = ?", (categoria_id,))
        conn.commit()
        conn.close()
        return True, "Categoria excluída."

    def reorder_categorias_impressoras(self, ids_ordered):
        conn = self.get_connection()
        for ordem, cat_id in enumerate(ids_ordered):
            conn.execute("UPDATE categorias_impressoras SET ordem = ? WHERE id = ?", (ordem, cat_id))
        conn.commit()
        conn.close()

    # ─── IMPRESSORAS ──────────────────────────────────────────────────────────

    def get_impressoras(self, categoria_id=None, apenas_em_estoque=False):
        conn = self.get_connection()
        query = """
            SELECT i.*, c.nome as categoria_nome
            FROM impressoras i
            JOIN categorias_impressoras c ON i.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        if categoria_id is not None:
            query += " AND i.categoria_id = ?"
            params.append(categoria_id)
        if apenas_em_estoque:
            query += " AND i.em_estoque = 1"
        query += " ORDER BY c.nome, i.modelo"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_impressora(self, impressora_id):
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM impressoras WHERE id = ?", (impressora_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_impressora(self, dados):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO impressoras
                (categoria_id, modelo, marca, sku, preco, imagem_path, em_estoque, quantidade)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            dados.get("categoria_id"),
            dados.get("modelo", "").strip(),
            dados.get("marca", "").strip(),
            dados.get("sku", "").strip(),
            dados.get("preco", "").strip(),
            dados.get("imagem_path", ""),
            1 if dados.get("em_estoque", True) else 0,
            dados.get("quantidade", "").strip(),
        ))
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return new_id

    def update_impressora(self, impressora_id, dados):
        conn = self.get_connection()
        conn.execute("""
            UPDATE impressoras SET
                categoria_id=?, modelo=?, marca=?, sku=?, preco=?,
                imagem_path=?, em_estoque=?, quantidade=?,
                atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            dados.get("categoria_id"),
            dados.get("modelo", "").strip(),
            dados.get("marca", "").strip(),
            dados.get("sku", "").strip(),
            dados.get("preco", "").strip(),
            dados.get("imagem_path", ""),
            1 if dados.get("em_estoque", True) else 0,
            dados.get("quantidade", "").strip(),
            impressora_id,
        ))
        conn.commit()
        conn.close()

    def set_estoque_impressora(self, impressora_id, em_estoque: bool):
        conn = self.get_connection()
        conn.execute(
            "UPDATE impressoras SET em_estoque = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if em_estoque else 0, impressora_id)
        )
        conn.commit()
        conn.close()

    def delete_impressora(self, impressora_id):
        conn = self.get_connection()
        row = conn.execute("SELECT imagem_path FROM impressoras WHERE id = ?", (impressora_id,)).fetchone()
        if row and row[0]:
            p = Path(row[0])
            p.unlink(missing_ok=True)
        conn.execute("DELETE FROM impressoras WHERE id = ?", (impressora_id,))
        conn.commit()
        conn.close()

    def save_impressora_image(self, source_path, impressora_id):
        dest_path = self.images_dir / f"impressora_{impressora_id}.jpg"
        try:
            from PIL import Image
            img = Image.open(source_path)
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.thumbnail((400, 400), Image.LANCZOS)
            img.save(str(dest_path), "JPEG", quality=82, optimize=True)
        except Exception:
            ext = Path(source_path).suffix.lower()
            dest_path = self.images_dir / f"impressora_{impressora_id}{ext}"
            shutil.copy2(source_path, dest_path)
        return str(dest_path)

    def duplicate_impressora(self, impressora_id, categoria_id=None, preco=None):
        imp = self.get_impressora(impressora_id)
        if not imp:
            return None
        dados = dict(imp)
        dados["imagem_path"] = ""
        for col in ("id", "criado_em", "atualizado_em", "categoria_nome"):
            dados.pop(col, None)
        if categoria_id is not None:
            dados["categoria_id"] = categoria_id
        if preco is not None:
            dados["preco"] = preco
        new_id = self.add_impressora(dados)
        old_img = imp.get("imagem_path", "")
        if old_img and Path(old_img).exists():
            ext = Path(old_img).suffix
            new_img = self.images_dir / f"impressora_{new_id}{ext}"
            shutil.copy2(old_img, str(new_img))
            conn = self.get_connection()
            conn.execute("UPDATE impressoras SET imagem_path = ? WHERE id = ?", (str(new_img), new_id))
            conn.commit()
            conn.close()
        return new_id