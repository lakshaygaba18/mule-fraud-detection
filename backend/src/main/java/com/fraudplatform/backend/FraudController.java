package com.fraudplatform.backend;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
public class FraudController {

    private final FraudMlClient fraudMlClient;
    private final AuditLogService auditLogService;

    public FraudController(FraudMlClient fraudMlClient, AuditLogService auditLogService) {
        this.fraudMlClient = fraudMlClient;
        this.auditLogService = auditLogService;
    }

    @GetMapping("/api/fraud-report")
    public Map<String, Object> getFraudReport() {
        return fraudMlClient.getFraudPredictions();
    }

    @GetMapping("/api/drift-report")
    public Map<String, Object> getDriftReport() {
        Map<String, Object> report = fraudMlClient.getDriftReport();
        auditLogService.logIfDrifted(report); // self-aware retrain-trigger
        return report;
    }

    @GetMapping("/api/audit-log")
    public List<AuditLogEntry> getAuditLog() {
        return auditLogService.getAllEntries();
    }
}