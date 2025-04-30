with open("10mb.txt", "w", encoding="utf-8") as f:
    for i in range(156504):
        f.write(f"Linha número {i:06d} - Texto de teste com variação no conteúdo.\n")
