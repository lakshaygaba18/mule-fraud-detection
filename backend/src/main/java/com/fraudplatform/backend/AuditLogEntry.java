package com.fraudplatform.backend;

import java.time.Instant;
import java.util.List;

public class AuditLogEntry {

    private final String id;
    private final Instant timestamp;
    private final String modelVersion;
    private final String overallStatus;
    private final Double scorePsi;
    private final List<String> alerts;
    private final String recommendation;
    private final String reviewStatus; // "pending_review" until a human acts on it

    public AuditLogEntry(String id, Instant timestamp, String modelVersion,
                          String overallStatus, Double scorePsi,
                          List<String> alerts, String recommendation) {
        this.id = id;
        this.timestamp = timestamp;
        this.modelVersion = modelVersion;
        this.overallStatus = overallStatus;
        this.scorePsi = scorePsi;
        this.alerts = alerts;
        this.recommendation = recommendation;
        this.reviewStatus = "pending_review";
    }

    public String getId() { return id; }
    public Instant getTimestamp() { return timestamp; }
    public String getModelVersion() { return modelVersion; }
    public String getOverallStatus() { return overallStatus; }
    public Double getScorePsi() { return scorePsi; }
    public List<String> getAlerts() { return alerts; }
    public String getRecommendation() { return recommendation; }
    public String getReviewStatus() { return reviewStatus; }
}