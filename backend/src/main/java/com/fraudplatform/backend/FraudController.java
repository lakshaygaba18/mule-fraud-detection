package com.fraudplatform.backend;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class FraudController {

    private final FraudMlClient fraudMlClient;

    public FraudController(FraudMlClient fraudMlClient) {
        this.fraudMlClient = fraudMlClient;
    }

    @GetMapping("/api/fraud-report")
    public Map<String, Object> getFraudReport() {
        return fraudMlClient.getFraudPredictions();
    }
        @GetMapping("/api/drift-report")
    public Map<String, Object> getDriftReport() {
        return fraudMlClient.getDriftReport();
    }
}