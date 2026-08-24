package com.fraudplatform.backend;

import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class AuditLogService {

    // In-memory for now -- swap for a JPA repository + DB later if needed.
    // CopyOnWriteArrayList is thread-safe for the low write-frequency this sees.
    private final List<AuditLogEntry> entries = new CopyOnWriteArrayList<>();

    private static final String CURRENT_MODEL_VERSION = "gnn_v1_baseline";

    /**
     * Called every time a drift-report is fetched. Only logs an entry when
     * the status is NOT stable -- this is the "self-aware" retrain-trigger:
     * the system notices its own drift and creates a compliance-style audit
     * record, without waiting for a human to notice a recall drop.
     */
    @SuppressWarnings("unchecked")
    public void logIfDrifted(java.util.Map<String, Object> driftReport) {
        String status = (String) driftReport.get("overall_status");
        if (status == null || status.equals("stable")) {
            return; // nothing to log -- model is behaving as expected
        }

        Double scorePsi = driftReport.get("score_psi") != null
                ? ((Number) driftReport.get("score_psi")).doubleValue()
                : null;

        List<String> alerts = driftReport.get("alerts") != null
                ? (List<String>) driftReport.get("alerts")
                : Collections.emptyList();

        String recommendation = status.equals("major_shift")
                ? "RETRAIN RECOMMENDED: input/output distribution has shifted significantly "
                  + "from the training baseline. Schedule a labeled-sample audit before trusting "
                  + "current scores, then retrain on recent data."
                : "MONITOR: moderate drift detected. No immediate retrain required, but "
                  + "re-check this report within the next few review cycles.";

        AuditLogEntry entry = new AuditLogEntry(
                UUID.randomUUID().toString(),
                Instant.now(),
                CURRENT_MODEL_VERSION,
                status,
                scorePsi,
                alerts,
                recommendation
        );

        entries.add(0, entry); // newest first
    }

    public List<AuditLogEntry> getAllEntries() {
        return new ArrayList<>(entries);
    }

    public int getPendingReviewCount() {
        return (int) entries.stream()
                .filter(e -> "pending_review".equals(e.getReviewStatus()))
                .count();
    }
}