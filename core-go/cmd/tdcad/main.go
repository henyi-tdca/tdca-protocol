// Command tdcad 是 TDCA 核心引擎守护进程（DCD-CORE-GO-001 + 融入方案 I-1）。
//
// 暴露 enforce/nca/nsfl 三包能力为 CLI——Python 侧通过子进程调用（接口熵=0）。
//
// 用法:
//   tdcad enforce check <card.json>        # 准入门禁校验
//   tdcad nca append <record.json>         # NCA 链追加
//   tdcad nca verify                       # 全链验证
//   tdcad nsfl eval <trigger> <signal>     # 熔断判定
//   tdcad version                          # 版本
//
// SPDX-License-Identifier: Apache-2.0
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/henyi-tdca/tdca-core-go/pkg/enforce"
	"github.com/henyi-tdca/tdca-core-go/pkg/nca"
	"github.com/henyi-tdca/tdca-core-go/pkg/nsfl"
)

const version = "1.0.0"

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "version":
		fmt.Println("tdcad", version)
	case "enforce":
		err = cmdEnforce(os.Args[2:])
	case "nca":
		err = cmdNca(os.Args[2:])
	case "nsfl":
		err = cmdNsfl(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Println(`tdcad - TDCA core engine daemon
Usage:
  tdcad enforce check <card.json>
  tdcad nca append <record.json>
  tdcad nca verify
  tdcad nsfl eval <trigger> <signal>
  tdcad version`)
}

func readJSON(path string, v any) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(raw, v)
}

// ---- enforce ----

func cmdEnforce(args []string) error {
	if len(args) != 2 || args[0] != "check" {
		return fmt.Errorf("usage: tdcad enforce check <card.json>")
	}
	raw, err := os.ReadFile(args[1])
	if err != nil {
		return err
	}
	gate := enforce.NewEntryGate()
	res, err := gate.Apply(raw)
	out, _ := json.MarshalIndent(res, "", "  ")
	fmt.Println(string(out))
	if res.Status != "PASS" {
		return fmt.Errorf("entry %s: %s", res.Status, res.Reason)
	}
	return nil
}

// ---- nca ----

func cmdNca(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: tdcad nca append|verify")
	}
	switch args[0] {
	case "append":
		if len(args) != 2 {
			return fmt.Errorf("usage: tdcad nca append <record.json>")
		}
		var rec nca.NcaRecord
		if err := readJSON(args[1], &rec); err != nil {
			return err
		}
		chain := nca.NewChain()
		if err := chain.Append(&rec); err != nil {
			return err
		}
		out := map[string]any{"status": "appended", "head": chain.Head(), "count": chain.Len()}
		b, _ := json.MarshalIndent(out, "", "  ")
		fmt.Println(string(b))
		return nil
	case "verify":
		// 无状态验证（单记录链）：从 stdin/文件 JSON 数组验证
		if len(args) == 2 {
			var recs []nca.NcaRecord
			if err := readJSON(args[1], &recs); err != nil {
				return err
			}
			chain := nca.NewChain()
			for _, r := range recs {
				if err := chain.Append(&r); err != nil {
					return err
				}
			}
			ok := chain.Verify()
			b, _ := json.MarshalIndent(map[string]any{"verify": ok, "count": chain.Len()}, "", "  ")
			fmt.Println(string(b))
			if !ok {
				return fmt.Errorf("chain verification failed")
			}
			return nil
		}
		return fmt.Errorf("usage: tdcad nca verify <records.json>")
	default:
		return fmt.Errorf("unknown nca subcommand: %s", args[0])
	}
}

// ---- nsfl ----

func cmdNsfl(args []string) error {
	// args = [eval, trigger, signal]（3 个：eval 子命令 + trigger + signal）
	if len(args) != 3 || args[0] != "eval" {
		return fmt.Errorf("usage: tdcad nsfl eval <trigger> <signal>")
	}
	engine := nsfl.NewFuseEngine()
	res := engine.Eval(args[1], args[2])
	out, _ := json.MarshalIndent(res, "", "  ")
	fmt.Println(string(out))
	if res.Blocked {
		return fmt.Errorf("nsfl %s", res.Action.Status)
	}
	return nil
}
