// App.js — Mobile React Native Companion for ASHA Field Workers
// Demonstrates offline-first SQLite/AsyncStorage persistence, auto-sync daemon & live sync badge
import React, { useEffect, useState } from "react";
import { View, Text, Button, StyleSheet, ScrollView } from "react-native";
import { startAutoSync, syncNow } from "./sync";
import { saveRecord, listRecords, pendingCount } from "./db";

export default function App() {
  const [list, setList] = useState([]);
  const [pending, setPending] = useState(0);

  const refresh = () => {
    setList(listRecords("beneficiary"));
    setPending(pendingCount());
  };

  useEffect(() => {
    // Start background sync every 60 seconds
    const stop = startAutoSync(60000);
    // Poll local state every 3 seconds for UI updates
    const t = setInterval(refresh, 3000);
    refresh();
    return () => {
      stop();
      clearInterval(t);
    };
  }, []);

  const addTest = () => {
    saveRecord(
      "beneficiary",
      {
        name: "Lakshmi",
        age: 24,
        edd: "2027-02-10",
        highRisk: false,
        village: "Thanjavur"
      },
      "9363302117"
    );
    refresh();
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>⚕️ ASHA Mobile EHR Companion</Text>
      
      <View style={[styles.badge, pending === 0 ? styles.badgeSuccess : styles.badgePending]}>
        <Text style={styles.badgeText}>
          {pending === 0 ? "✅ All data synced to server" : `⏳ ${pending} records waiting to sync`}
        </Text>
      </View>

      <View style={styles.btnRow}>
        <Button title="Add Beneficiary (Offline)" onPress={addTest} color="#0284c7" />
      </View>

      <View style={styles.btnRow}>
        <Button
          title="Sync Now"
          onPress={async () => {
            await syncNow();
            refresh();
          }}
          color="#16a34a"
        />
      </View>

      <Text style={styles.subhead}>Beneficiary Records ({list.length}):</Text>
      {list.map((r) => (
        <View key={r.id} style={styles.recordCard}>
          <Text style={styles.recordName}>{r.data.name} (Age {r.data.age})</Text>
          <Text style={styles.recordVillage}>Village: {r.data.village || "Thanjavur"}</Text>
          <Text style={r.dirty ? styles.statusDirty : styles.statusClean}>
            {r.dirty ? "⚠️ Not synced (Local Only)" : "✅ Synced with Central Server"}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    marginTop: 40,
    backgroundColor: "#f8fafc"
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 16,
    color: "#0f172a"
  },
  badge: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16
  },
  badgeSuccess: {
    backgroundColor: "#dcfce7",
    borderColor: "#86efac",
    borderWidth: 1
  },
  badgePending: {
    backgroundColor: "#fef9c3",
    borderColor: "#fde047",
    borderWidth: 1
  },
  badgeText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1e293b"
  },
  btnRow: {
    marginVertical: 6
  },
  subhead: {
    fontSize: 16,
    fontWeight: "700",
    marginTop: 20,
    marginBottom: 10,
    color: "#334155"
  },
  recordCard: {
    backgroundColor: "#ffffff",
    padding: 14,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  recordName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0f172a"
  },
  recordVillage: {
    fontSize: 13,
    color: "#64748b",
    marginVertical: 2
  },
  statusDirty: {
    fontSize: 13,
    color: "#d97706",
    fontWeight: "600",
    marginTop: 4
  },
  statusClean: {
    fontSize: 13,
    color: "#16a34a",
    fontWeight: "600",
    marginTop: 4
  }
});
