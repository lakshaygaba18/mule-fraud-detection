package com.fraudplatform.backend;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Map;

@Service
public class FraudMlClient {

    private final RestClient restClient;

    public FraudMlClient(
            @Value("${ml.service.url}") String mlServiceUrl) {

        this.restClient = RestClient.builder()
                .baseUrl(mlServiceUrl)
                .build();
    }

    public Map<String, Object> getFraudPredictions() {
        return restClient.post()
                .uri("/predict")
                .retrieve()
                .body(Map.class);
    }

    public Map<String, Object> getDriftReport() {
        return restClient.get()
                .uri("/drift-report")
                .retrieve()
                .body(Map.class);
    }

    public Map<String, Object> getNetwork() {
        return restClient.get()
                .uri("/network")
                .retrieve()
                .body(Map.class);
    }
}