import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/fraud_account.dart';
import '../models/drift_report.dart';

class FraudApiService {
  static const String baseUrl = 'http://localhost:8080';

  Future<FraudReport> fetchFraudReport() async {
    final response = await http.get(Uri.parse('$baseUrl/api/fraud-report'));

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      return FraudReport.fromJson(data);
    } else {
      throw Exception('Failed to load fraud report: ${response.statusCode}');
    }
  }

  Future<DriftReport> fetchDriftReport() async {
    final response = await http.get(Uri.parse('$baseUrl/api/drift-report'));

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      return DriftReport.fromJson(data);
    } else {
      throw Exception('Failed to load drift report: ${response.statusCode}');
    }
  }
}