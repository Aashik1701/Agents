#!/usr/bin/env python3
"""
Security Configuration Validation Script for EMS Agent
Validates security settings and provides recommendations
"""

import os
import sys
import re
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityValidator:
    """Validates security configuration and settings"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def validate_environment(self) -> Tuple[bool, List[str], List[str]]:
        """Validate all security environment variables"""
        logger.info("Starting security configuration validation...")
        
        # Critical security checks
        self._check_jwt_secret()
        self._check_encryption_key()
        self._check_database_credentials()
        self._check_admin_credentials()
        self._check_ssl_configuration()
        self._check_rate_limiting()
        self._check_password_policies()
        self._check_network_security()
        self._check_logging_security()
        
        # Security best practices
        self._check_environment_type()
        self._check_debug_settings()
        self._check_cors_settings()
        
        return len(self.issues) == 0, self.issues, self.warnings
    
    def _check_jwt_secret(self):
        """Check JWT secret key security"""
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        
        if not jwt_secret:
            self.issues.append("JWT_SECRET_KEY is not set")
            return
            
        if len(jwt_secret) < 32:
            self.issues.append("JWT_SECRET_KEY is too short (minimum 32 characters)")
        elif jwt_secret in ['your-super-secret-jwt-key-change-in-production', 'default', 'secret']:
            self.issues.append("JWT_SECRET_KEY uses default/weak value - change immediately!")
        else:
            self.passed.append("JWT_SECRET_KEY length is adequate")
    
    def _check_encryption_key(self):
        """Check encryption key security"""
        enc_key = os.getenv('ENCRYPTION_KEY', '')
        
        if not enc_key:
            self.issues.append("ENCRYPTION_KEY is not set")
            return
            
        if len(enc_key) < 32:
            self.issues.append("ENCRYPTION_KEY is too short (minimum 32 characters)")
        elif enc_key in ['your-32-char-encryption-key', 'default']:
            self.issues.append("ENCRYPTION_KEY uses default value - change immediately!")
        else:
            self.passed.append("ENCRYPTION_KEY is properly configured")
    
    def _check_database_credentials(self):
        """Check database security settings"""
        mongo_uri = os.getenv('MONGODB_URI', '')
        mongo_user = os.getenv('MONGO_ROOT_USERNAME', '')
        mongo_pass = os.getenv('MONGO_ROOT_PASSWORD', '')
        
        if not mongo_uri:
            self.issues.append("MONGODB_URI is not set")
        elif 'password123' in mongo_uri or 'admin:admin' in mongo_uri:
            self.issues.append("MongoDB URI contains default/weak credentials")
        else:
            self.passed.append("MongoDB URI is configured")
            
        if mongo_pass in ['password', 'admin', 'password123', '123456']:
            self.issues.append("MongoDB password is weak or default")
        elif len(mongo_pass) < 12:
            self.warnings.append("MongoDB password should be at least 12 characters")
        else:
            self.passed.append("MongoDB password meets minimum requirements")
    
    def _check_admin_credentials(self):
        """Check admin account security"""
        admin_user = os.getenv('ADMIN_USERNAME', 'admin')
        admin_pass = os.getenv('ADMIN_PASSWORD', '')
        
        if admin_user == 'admin':
            self.warnings.append("Consider changing default admin username")
            
        if not admin_pass:
            self.issues.append("ADMIN_PASSWORD is not set")
        elif admin_pass in ['admin', 'password', 'admin123', '123456']:
            self.issues.append("Admin password is weak or default - change immediately!")
        elif len(admin_pass) < 12:
            self.warnings.append("Admin password should be at least 12 characters")
        else:
            self.passed.append("Admin password meets security requirements")
    
    def _check_ssl_configuration(self):
        """Check SSL/TLS configuration"""
        enable_https = os.getenv('ENABLE_HTTPS', 'false').lower()
        force_https = os.getenv('FORCE_HTTPS', 'false').lower()
        ssl_cert = os.getenv('SSL_CERT_PATH', '')
        ssl_key = os.getenv('SSL_KEY_PATH', '')
        
        if enable_https != 'true':
            self.warnings.append("HTTPS is not enabled - recommended for production")
        else:
            self.passed.append("HTTPS is enabled")
            
        if force_https != 'true' and enable_https == 'true':
            self.warnings.append("Consider enabling FORCE_HTTPS for production")
            
        if enable_https == 'true' and (not ssl_cert or not ssl_key):
            self.issues.append("SSL enabled but certificate paths not configured")
    
    def _check_rate_limiting(self):
        """Check rate limiting configuration"""
        api_rate_limit = int(os.getenv('API_RATE_LIMIT', '0'))
        login_rate_limit = int(os.getenv('LOGIN_RATE_LIMIT', '0'))
        
        if api_rate_limit == 0:
            self.warnings.append("API rate limiting is not configured")
        elif api_rate_limit > 1000:
            self.warnings.append("API rate limit is very high - consider lowering for production")
        else:
            self.passed.append("API rate limiting is configured")
            
        if login_rate_limit == 0:
            self.warnings.append("Login rate limiting is not configured")
        elif login_rate_limit > 10:
            self.warnings.append("Login rate limit is high - consider stricter limits")
        else:
            self.passed.append("Login rate limiting is configured")
    
    def _check_password_policies(self):
        """Check password policy configuration"""
        min_length = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
        require_upper = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'false').lower() == 'true'
        require_lower = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'false').lower() == 'true'
        require_numbers = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'false').lower() == 'true'
        require_symbols = os.getenv('PASSWORD_REQUIRE_SYMBOLS', 'false').lower() == 'true'
        
        if min_length < 12:
            self.warnings.append("Password minimum length should be at least 12 characters")
        else:
            self.passed.append("Password minimum length is adequate")
            
        if not all([require_upper, require_lower, require_numbers, require_symbols]):
            self.warnings.append("Password policy should require uppercase, lowercase, numbers, and symbols")
        else:
            self.passed.append("Strong password policy is configured")
    
    def _check_network_security(self):
        """Check network security settings"""
        cors_origins = os.getenv('CORS_ORIGINS', '')
        ip_whitelist = os.getenv('ENABLE_IP_WHITELIST', 'false').lower() == 'true'
        allowed_ips = os.getenv('ALLOWED_IP_RANGES', '')
        
        if '*' in cors_origins or 'http://' in cors_origins:
            self.warnings.append("CORS origins should be restrictive and use HTTPS in production")
        elif cors_origins:
            self.passed.append("CORS origins are configured")
            
        if not ip_whitelist and os.getenv('ENVIRONMENT') == 'production':
            self.warnings.append("Consider enabling IP whitelisting for production")
        elif ip_whitelist and not allowed_ips:
            self.issues.append("IP whitelist enabled but no allowed IP ranges configured")
    
    def _check_logging_security(self):
        """Check security logging configuration"""
        audit_logging = os.getenv('ENABLE_AUDIT_LOGGING', 'false').lower() == 'true'
        security_monitoring = os.getenv('ENABLE_SECURITY_MONITORING', 'false').lower() == 'true'
        intrusion_detection = os.getenv('ENABLE_INTRUSION_DETECTION', 'false').lower() == 'true'
        
        if not audit_logging:
            self.warnings.append("Audit logging is not enabled")
        else:
            self.passed.append("Audit logging is enabled")
            
        if not security_monitoring:
            self.warnings.append("Security monitoring is not enabled")
        else:
            self.passed.append("Security monitoring is enabled")
            
        if not intrusion_detection:
            self.warnings.append("Intrusion detection is not enabled")
        else:
            self.passed.append("Intrusion detection is enabled")
    
    def _check_environment_type(self):
        """Check environment configuration"""
        environment = os.getenv('ENVIRONMENT', 'development')
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        if environment == 'development' and not debug:
            self.warnings.append("Development environment detected but debug is disabled")
        elif environment == 'production' and debug:
            self.issues.append("Production environment has debug enabled - security risk!")
        else:
            self.passed.append("Environment type is properly configured")
    
    def _check_debug_settings(self):
        """Check debug-related security settings"""
        debug_toolbar = os.getenv('ENABLE_DEBUG_TOOLBAR', 'false').lower() == 'true'
        profiling = os.getenv('ENABLE_PROFILING', 'false').lower() == 'true'
        mock_services = os.getenv('MOCK_EXTERNAL_SERVICES', 'false').lower() == 'true'
        
        if os.getenv('ENVIRONMENT') == 'production':
            if debug_toolbar:
                self.issues.append("Debug toolbar is enabled in production!")
            if profiling:
                self.issues.append("Profiling is enabled in production!")
            if mock_services:
                self.issues.append("External service mocking is enabled in production!")
        
        if not any([debug_toolbar, profiling, mock_services]):
            self.passed.append("Debug features are properly disabled")
    
    def _check_cors_settings(self):
        """Check CORS security settings"""
        cors_origins = os.getenv('CORS_ORIGINS', '')
        
        if not cors_origins:
            self.warnings.append("CORS origins not configured")
        elif cors_origins == '*':
            self.issues.append("CORS allows all origins - major security risk!")
        elif 'http://' in cors_origins and os.getenv('ENVIRONMENT') == 'production':
            self.warnings.append("CORS allows HTTP origins in production - use HTTPS")
        else:
            self.passed.append("CORS origins are properly configured")

def main():
    """Main validation function"""
    print("🔒 EMS Agent Security Configuration Validator")
    print("=" * 50)
    
    validator = SecurityValidator()
    is_secure, issues, warnings = validator.validate_environment()
    
    # Display results
    if validator.passed:
        print("\n✅ PASSED CHECKS:")
        for check in validator.passed:
            print(f"  ✓ {check}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    if issues:
        print("\n❌ CRITICAL ISSUES:")
        for issue in issues:
            print(f"  ❌ {issue}")
    
    # Security score
    total_checks = len(validator.passed) + len(warnings) + len(issues)
    security_score = (len(validator.passed) / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n📊 SECURITY SCORE: {security_score:.1f}%")
    
    if is_secure:
        print("✅ Security configuration is acceptable")
        print("\n🔧 RECOMMENDATIONS:")
        print("  • Regularly rotate secrets and passwords")
        print("  • Enable comprehensive monitoring and alerting")
        print("  • Perform regular security audits")
        print("  • Keep all dependencies updated")
        return 0
    else:
        print("❌ Security configuration has critical issues!")
        print("\n🚨 IMMEDIATE ACTION REQUIRED:")
        print("  • Fix all critical issues before deployment")
        print("  • Review and update security policies")
        print("  • Enable proper monitoring and logging")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
