class NetworkGraph {
  final int nodeCount;
  final int edgeCount;
  final List<NetworkNode> nodes;
  final List<NetworkEdge> edges;

  NetworkGraph({
    required this.nodeCount,
    required this.edgeCount,
    required this.nodes,
    required this.edges,
  });

  factory NetworkGraph.fromJson(Map<String, dynamic> json) {
    return NetworkGraph(
      nodeCount: (json['nodeCount'] ?? 0) as int,
      edgeCount: (json['edgeCount'] ?? 0) as int,

      nodes: (json['nodes'] as List<dynamic>? ?? [])
          .map(
            (node) => NetworkNode.fromJson(
              Map<String, dynamic>.from(node),
            ),
          )
          .toList(),

      edges: (json['edges'] as List<dynamic>? ?? [])
          .map(
            (edge) => NetworkEdge.fromJson(
              Map<String, dynamic>.from(edge),
            ),
          )
          .toList(),
    );
  }
}

class NetworkNode {
  final String id;
  final double riskScore;
  final String riskLevel;
  final int label;

  NetworkNode({
    required this.id,
    required this.riskScore,
    required this.riskLevel,
    required this.label,
  });

  factory NetworkNode.fromJson(Map<String, dynamic> json) {
    final rawScore = json['riskScore'];

    double score = 0;

    if (rawScore is num) {
      score = rawScore.toDouble();
    } else if (rawScore is String) {
      score = double.tryParse(rawScore) ?? 0;
    }

    return NetworkNode(
      id: json['id']?.toString() ?? '',
      riskScore: score,
      riskLevel: json['riskLevel']?.toString() ?? 'UNKNOWN',
      label: json['label'] is num
          ? (json['label'] as num).toInt()
          : 0,
    );
  }
}

class NetworkEdge {
  final String source;
  final String target;
  final double amount;

  NetworkEdge({
    required this.source,
    required this.target,
    required this.amount,
  });

  factory NetworkEdge.fromJson(Map<String, dynamic> json) {
    final rawAmount = json['amount'];

    double amount = 0;

    if (rawAmount is num) {
      amount = rawAmount.toDouble();
    } else if (rawAmount is String) {
      amount = double.tryParse(rawAmount) ?? 0;
    }

    return NetworkEdge(
      source: json['source']?.toString() ?? '',
      target: json['target']?.toString() ?? '',
      amount: amount,
    );
  }
}