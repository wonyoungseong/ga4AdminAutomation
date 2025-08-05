"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Key, Plus, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";
import { typeSafeApiClient, ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";

interface ServiceAccountFormData {
  name: string;
  email: string;
  description: string;
  client_id: string;
  project_id: string;
  credentials_file: File | null;
}

export default function AddServiceAccountPage() {
  const { user } = useAuth();
  const router = useRouter();
  
  const [formData, setFormData] = useState<ServiceAccountFormData>({
    name: "",
    email: "",
    description: "",
    client_id: "",
    project_id: "",
    credentials_file: null
  });
  
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const validateForm = (): boolean => {
    const errors: { [key: string]: string } = {};

    if (!formData.name.trim()) errors.name = "서비스 계정 이름을 입력하세요.";
    if (!formData.email.trim()) errors.email = "서비스 계정 이메일을 입력하세요.";
    if (!formData.email.includes("@")) errors.email = "올바른 이메일 형식을 입력하세요.";
    if (!formData.project_id.trim()) errors.project_id = "프로젝트 ID를 입력하세요.";
    if (!formData.credentials_file) {
      errors.credentials_file = "서비스 계정 인증 파일을 업로드하세요.";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    try {
      setIsLoading(true);
      setErrorMessage("");
      
      const formDataToSend = new FormData();
      formDataToSend.append('name', formData.name);
      formDataToSend.append('email', formData.email);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('project_id', formData.project_id);
      if (formData.client_id) {
        formDataToSend.append('client_id', formData.client_id);
      }
      if (formData.credentials_file) {
        formDataToSend.append('credentials_file', formData.credentials_file);
      }

      await typeSafeApiClient.createServiceAccount(formDataToSend);
      
      setIsSuccess(true);
      setSuccessMessage("서비스 계정이 성공적으로 생성되었습니다!");
      
      // 3초 후 서비스 계정 목록 페이지로 이동
      setTimeout(() => {
        router.push("/dashboard/service-accounts");
      }, 3000);
      
    } catch (error) {
      console.error("서비스 계정 생성 실패:", error);
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("서비스 계정 생성 중 오류가 발생했습니다.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    router.back();
  };

  if (isSuccess) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={handleGoBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-green-600">성공!</h1>
            <p className="text-muted-foreground">서비스 계정이 생성되었습니다</p>
          </div>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="text-center space-y-4">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
              <h2 className="text-xl font-semibold">{successMessage}</h2>
              <p className="text-muted-foreground">
                잠시 후 서비스 계정 목록 페이지로 이동합니다...
              </p>
              <Button onClick={() => router.push("/dashboard/service-accounts")}>
                바로 이동하기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={handleGoBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">서비스 계정 추가</h1>
          <p className="text-muted-foreground">새로운 Google Analytics 4 서비스 계정을 추가합니다</p>
        </div>
      </div>

      {errorMessage && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {errorMessage}
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            서비스 계정 정보
          </CardTitle>
          <CardDescription>
            Google Cloud Console에서 생성한 서비스 계정의 정보를 입력하세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">서비스 계정 이름 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="예: GA4 서비스 계정"
                  disabled={isLoading}
                />
                {formErrors.name && <p className="text-sm text-red-600">{formErrors.name}</p>}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">서비스 계정 이메일 *</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="예: service-account@project.iam.gserviceaccount.com"
                  disabled={isLoading}
                />
                {formErrors.email && <p className="text-sm text-red-600">{formErrors.email}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="project_id">프로젝트 ID *</Label>
              <Input
                id="project_id"
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                placeholder="예: my-analytics-project"
                disabled={isLoading}
              />
              {formErrors.project_id && <p className="text-sm text-red-600">{formErrors.project_id}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">설명</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="서비스 계정에 대한 설명을 입력하세요..."
                rows={3}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="credentials_file">서비스 계정 인증 파일 (JSON) *</Label>
              <Input
                id="credentials_file"
                type="file"
                accept=".json"
                onChange={(e) => setFormData({ ...formData, credentials_file: e.target.files?.[0] || null })}
                disabled={isLoading}
              />
              {formErrors.credentials_file && <p className="text-sm text-red-600">{formErrors.credentials_file}</p>}
              <p className="text-sm text-muted-foreground">
                Google Cloud Console에서 다운로드한 서비스 계정 JSON 키 파일을 업로드하세요.
              </p>
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleGoBack}
                disabled={isLoading}
              >
                취소
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    생성 중...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    서비스 계정 생성
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}