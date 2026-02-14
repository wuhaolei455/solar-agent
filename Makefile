.PHONY: help install run list

# 默认目标：显示帮助
help:
	@echo "============================================"
	@echo "  Solar Agent - Demo 管理工具"
	@echo "============================================"
	@echo ""
	@echo "用法:"
	@echo "  make list              列出所有可用的 demo"
	@echo "  make install DEMO=01   安装指定 demo 的依赖"
	@echo "  make run DEMO=01       运行指定 demo"
	@echo "  make setup DEMO=01     安装依赖并运行 demo"
	@echo ""

# 列出所有 demo
list:
	@echo "可用的 Demo："
	@echo "-------------------------------------------"
	@for dir in demos/*/; do \
		name=$$(basename $$dir); \
		if [ -f "$$dir/main.py" ]; then \
			echo "  $$name"; \
		fi; \
	done
	@echo "-------------------------------------------"

# 安装指定 demo 的依赖
install:
	@if [ -z "$(DEMO)" ]; then \
		echo "错误：请指定 DEMO 编号，例如: make install DEMO=01"; \
		exit 1; \
	fi
	@DEMO_DIR=$$(find demos -maxdepth 1 -type d -name "$(DEMO)*" | head -1); \
	if [ -z "$$DEMO_DIR" ]; then \
		echo "错误：未找到编号为 $(DEMO) 的 demo"; \
		exit 1; \
	fi; \
	echo "正在安装 $$DEMO_DIR 的依赖..."; \
	pip install -r $$DEMO_DIR/requirements.txt

# 运行指定 demo
run:
	@if [ -z "$(DEMO)" ]; then \
		echo "错误：请指定 DEMO 编号，例如: make run DEMO=01"; \
		exit 1; \
	fi
	@DEMO_DIR=$$(find demos -maxdepth 1 -type d -name "$(DEMO)*" | head -1); \
	if [ -z "$$DEMO_DIR" ]; then \
		echo "错误：未找到编号为 $(DEMO) 的 demo"; \
		exit 1; \
	fi; \
	echo "正在运行 $$DEMO_DIR/main.py ..."; \
	echo "============================================"; \
	python $$DEMO_DIR/main.py

# 安装依赖并运行
setup:
	@$(MAKE) install DEMO=$(DEMO)
	@$(MAKE) run DEMO=$(DEMO)
