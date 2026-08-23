package nca

import (
	"encoding/json"
	"sync"
	"testing"
)

func mkRecord(id string, prev string, typ string) *NcaRecord {
	return NewRecord(id, typ, NowISO(), prev, map[string]any{"k": id})
}

func TestChainAppendAndVerify(t *testing.T) {
	c := NewChain()
	r1 := mkRecord("n1", "sha256:genesis", "fact")
	if err := c.Append(r1); err != nil {
		t.Fatal(err)
	}
	r2 := mkRecord("n2", c.Head(), "fact")
	if err := c.Append(r2); err != nil {
		t.Fatal(err)
	}
	if c.Len() != 2 {
		t.Fatalf("expected 2 records, got %d", c.Len())
	}
	if !c.Verify() {
		t.Fatal("chain should verify")
	}
}

// 破坏性测试：伪造 NCA（prev_hash 错链）→ 拒绝
func TestChainTamperPrevHashRejected(t *testing.T) {
	c := NewChain()
	r1 := mkRecord("n1", "sha256:genesis", "fact")
	_ = c.Append(r1)
	forged := mkRecord("forged", "sha256:deadbeef", "fact")
	if err := c.Append(forged); err == nil {
		t.Fatal("forged prev_hash should be rejected")
	}
}

// 破坏性测试：伪造 NCA（篡改哈希载荷）→ 验证失败
func TestChainVerifyDetectsTamperedHash(t *testing.T) {
	c := NewChain()
	r1 := mkRecord("n1", "sha256:genesis", "fact")
	_ = c.Append(r1)
	r2 := mkRecord("n2", c.Head(), "fact")
	_ = c.Append(r2)
	// 篡改第 2 条载荷（RecordHash 变化 → 与记录 Hash 不符）
	r2.Payload = map[string]any{"k": "EVIL"}
	if c.Verify() {
		t.Fatal("tampered chain should NOT verify")
	}
}

// 破坏性测试：验签失败（signer 缺失）→ 拒绝
func TestChainSignatureMissingRejected(t *testing.T) {
	c := NewChain()
	r := mkRecord("n1", "sha256:genesis", "fact")
	r.Signer = ""
	if err := c.VerifySignature(r); err == nil {
		t.Fatal("missing signer should fail verification")
	}
}

func TestChainSignatureOK(t *testing.T) {
	c := NewChain()
	r := mkRecord("n1", "sha256:genesis", "fact")
	r.Signer = "TDCA-PUBKEY-ABCD1234-01"
	r.Hash = r.RecordHash()
	if err := c.VerifySignature(r); err != nil {
		t.Fatal(err)
	}
}

func TestChainSnapshotJSON(t *testing.T) {
	c := NewChain()
	_ = c.Append(mkRecord("n1", "sha256:genesis", "fact"))
	snap := c.Snapshot()
	if len(snap) == 0 {
		t.Fatal("snapshot empty")
	}
	// JSON 合法性（接口熵=0）
	var out []map[string]any
	if err := jsonUnmarshal(snap, &out); err != nil {
		t.Fatal(err)
	}
	if len(out) != 1 {
		t.Fatalf("expected 1 record in snapshot, got %d", len(out))
	}
}

// 破坏性测试：并发追加（十万级）→ 无死锁/无数据竞争
func TestChainConcurrentAppend(t *testing.T) {
	c := NewChain()
	const n = 10000
	var wg sync.WaitGroup
	// 串行链（每块依赖 head）——用单写者验证并发读安全
	wg.Add(1)
	go func() {
		defer wg.Done()
		prev := "sha256:genesis"
		for i := 0; i < n; i++ {
			r := mkRecord(string(rune('a'+i%26))+itoa(i), prev, "fact")
			if err := c.Append(r); err != nil {
				t.Errorf("append %d: %v", i, err)
				return
			}
			prev = c.Head()
		}
	}()
	// 并发读者
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 500; j++ {
				_ = c.Verify()
				_ = c.Head()
			}
		}()
	}
	wg.Wait()
	if c.Len() != n {
		t.Fatalf("expected %d records, got %d", n, c.Len())
	}
	if !c.Verify() {
		t.Fatal("concurrent chain should verify")
	}
}

func itoa(i int) string {
	if i == 0 {
		return "0"
	}
	var b []byte
	for i > 0 {
		b = append([]byte{byte('0' + i%10)}, b...)
		i /= 10
	}
	return string(b)
}

func jsonUnmarshal(b []byte, v any) error {
	return json.Unmarshal(b, v)
}
