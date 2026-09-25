// credbind-check 条例《租户与环境作用域凭证绑定条例》R2 规格洁净扫描器
// （交办件 TDCA-HANDOFF-EXEC-TENANT-CRED-BIND-IMPL-001）。
//
// 用法：
//
//	credbind-check <路径>   递归扫描该路径下 *.json 工具规格件（{"name","inputSchema"}），
//	                        对每个规格跑 CheckSpecClean（R2 规格洁净）
//	credbind-check selftest 对内建核心工具规格自查（须 0 命中）
//
// 退出码语义（丙案，GSEQ-2818：失败一律 1，细分原因写进输出文本，不塞进退出码）：
//
//	0 = CHECK PASS
//	1 = CHECK FAIL（失败统称：目标路径不存在 / 零扫描即失守 / 检出违规；
//	    细分原因见输出文本：not found / ZERO-SCAN / VIOLATION）
//	2 = 用法错误 / 空输入（未提供目标；保留 2 对齐 Go 侧惯例，同 tdcad）
//
// 输出确定性（A-3）：文件列表排序、命中随序、无时间戳，同输入同输出逐字节一致。
//
// SPDX-License-Identifier: Apache-2.0
package main

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/henyi-tdca/tdca-core-go/pkg/mcp"
)

// 退出码语义（见文件头注释；丙案 GSEQ-2818：失败一律 1，用法错保留 2 对齐 Go 惯例）
const (
	exitPass      = 0 // CHECK PASS
	exitUsage     = 2 // 用法错误 / 空输入
	exitNoTarget  = 1 // 目标路径不存在（失败统称 1；细分见输出文本 not found）
	exitZeroScan  = 1 // 零扫描即失守（失败统称 1；细分见输出文本 ZERO-SCAN）
	exitCheckFail = 1 // CHECK FAIL（检出违规；细分见输出文本 VIOLATION 逐条）
)

const usageLine = "usage: credbind-check <路径> | credbind-check selftest"

// specFile 待检工具规格件（形如 {"name","inputSchema"}）
type specFile struct {
	Name        string      `json:"name"`
	InputSchema *mcp.Schema `json:"inputSchema"`
}

// Run 扫描入口（可测函数）：返回确定性输出与退出码；main 仅负责打印与退出码映射。
func Run(args []string) (string, int) {
	if len(args) != 1 {
		return usageLine + "\n", exitUsage
	}
	if args[0] == "selftest" {
		return runSelftest()
	}
	return scanPath(args[0])
}

// runSelftest 内建核心工具规格自查（R2：0 命中方为过）
func runSelftest() (string, int) {
	tools := mcp.NewServer().Tools()
	var b strings.Builder
	hits := 0
	for _, t := range tools {
		if err := mcp.CheckSpecClean(t.InputSchema); err != nil {
			fmt.Fprintf(&b, "VIOLATION selftest tool=%q: %v\n", t.Name, err)
			hits++
		}
	}
	fmt.Fprintf(&b, "selftest: %d core tool spec(s) checked, %d violation(s)\n", len(tools), hits)
	if hits > 0 {
		b.WriteString("CHECK FAIL\n")
		return b.String(), exitCheckFail
	}
	b.WriteString("CHECK PASS\n")
	return b.String(), exitPass
}

// scanPath 递归扫描 root 下 *.json 规格件并逐一跑 CheckSpecClean
func scanPath(root string) (string, int) {
	if _, err := os.Stat(root); err != nil {
		return fmt.Sprintf("credbind-check: target %q not found\n", filepath.ToSlash(root)), exitNoTarget
	}
	var files []string
	_ = filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if strings.EqualFold(filepath.Ext(p), ".json") {
			files = append(files, p)
		}
		return nil
	})
	sort.Strings(files) // 确定性：文件列表排序
	scanned := 0
	var violations []string
	for _, f := range files {
		raw, err := os.ReadFile(f)
		if err != nil {
			continue
		}
		var spec specFile
		// 非工具规格件（解析失败 / 缺 name / 缺 inputSchema）不计入扫描
		if err := json.Unmarshal(raw, &spec); err != nil || spec.Name == "" || spec.InputSchema == nil {
			continue
		}
		scanned++
		if err := mcp.CheckSpecClean(spec.InputSchema); err != nil {
			violations = append(violations,
				fmt.Sprintf("VIOLATION %s tool=%q: %v\n", filepath.ToSlash(f), spec.Name, err))
		}
	}
	var b strings.Builder
	fmt.Fprintf(&b, "credbind-check: scanned %d tool spec(s) under %q\n", scanned, filepath.ToSlash(root))
	for _, v := range violations { // 命中已随排序文件序产出（每规格至多首命中一条）
		b.WriteString(v)
	}
	if scanned == 0 {
		b.WriteString("ZERO-SCAN: path exists but no tool spec found\n")
		return b.String(), exitZeroScan
	}
	if len(violations) > 0 {
		b.WriteString("CHECK FAIL\n")
		return b.String(), exitCheckFail
	}
	b.WriteString("CHECK PASS\n")
	return b.String(), exitPass
}

func main() {
	out, code := Run(os.Args[1:])
	fmt.Print(out)
	os.Exit(code)
}
