import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/fraud_account.dart';
import '../models/drift_report.dart';
import '../models/network_graph.dart';

class FraudApiService {
  // Local development backend
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8080',
  );

  Future<FraudReport> fetchFraudReport() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/fraud-report'),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data =
          jsonDecode(response.body);

      return FraudReport.fromJson(data);
    }

    throw Exception(
      'Failed to load fraud report: ${response.statusCode}',
    );
  }

  Future<DriftReport> fetchDriftReport() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/drift-report'),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data =
          jsonDecode(response.body);

      return DriftReport.fromJson(data);
    }

    throw Exception(
      'Failed to load drift report: ${response.statusCode}',
    );
  }

  Future<NetworkGraph> fetchNetwork() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/network'),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data =
          jsonDecode(response.body);

      return NetworkGraph.fromJson(data);
    }

    throw Exception(
      'Failed to load network graph: ${response.statusCode}',
    );
  }
}