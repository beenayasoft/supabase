# Blueprint - Module 1: Gestion des Utilisateurs et des Rôles

## Analyse de l'existant

### Backend (Django)
- **Modèles existants**: 
  - `User`: Modèle utilisateur personnalisé avec email comme identifiant
  - `Role`: Modèle pour les rôles (Administrateur, Gérant, etc.)
  - `UserRole`: Relation M2M entre User et Role
  - `Invitation`: Modèle pour les invitations d'utilisateurs

- **Migrations existantes**:
  - Migration pour créer les rôles prédéfinis (0005_initial_roles.py)
  - Migration pour ajouter les statuts d'utilisateurs (active, inactive, pending)

- **Permissions**:
  - `IsAdministrator`: Permission pour limiter l'accès aux administrateurs
  - `IsAdminOrSuperUser`: Permission pour limiter l'accès aux administrateurs ou superutilisateurs

- **Endpoints existants**: 
  - Login/Refresh/Register/UserInfo
  - Documentation d'API mentionnant des endpoints pour gérer les utilisateurs et les invitations

### Frontend (React/TypeScript)
- **Composants existants**:
  - `UserManagement`: Gestion des utilisateurs
  - `InviteUserModal`: Formulaire d'invitation
  - `AdminMetrics`: Métriques sur les utilisateurs
  - `UserDetailModal`: Détails d'un utilisateur
  - `RoleBadges`: Affichage des rôles d'un utilisateur
  - `UserStatusBadge`: Affichage du statut d'un utilisateur

- **API Client**:
  - `admin.ts`: Client API pour les fonctionnalités d'administration
  - Fonctions pour gérer les utilisateurs et les invitations

- **Hooks**:
  - `useAdmin`: Hook pour gérer les fonctionnalités d'administration

## Modifications à apporter

### Backend (Django)

1. **Endpoints à ajouter/compléter**:
   - `POST /auth/invitations/`: Créer une invitation (pour l'admin)
   - `GET /auth/invitations/`: Lister les invitations
   - `POST /auth/invitations/{id}/resend/`: Renvoyer une invitation
   - `GET /auth/invitations/{token}/`: Valider un token d'invitation
   - `POST /auth/invitations/{token}/accept/`: Accepter une invitation et créer un compte
   - `GET /auth/users/`: Lister les utilisateurs
   - `PATCH /auth/users/{id}/`: Mettre à jour un utilisateur
   - `POST /auth/users/{id}/activate/`: Activer un utilisateur
   - `POST /auth/users/{id}/deactivate/`: Désactiver un utilisateur
   - `POST /auth/users/{id}/update_roles/`: Mettre à jour les rôles d'un utilisateur

2. **Serializers à ajouter**:
   - `InvitationSerializer`: Pour créer/afficher les invitations
   - `InvitationAcceptSerializer`: Pour accepter les invitations
   - `UserRoleSerializer`: Pour gérer les rôles des utilisateurs
   - `UserDetailSerializer`: Pour afficher les détails complets d'un utilisateur

3. **Vues à ajouter**:
   - `InvitationViewSet`: CRUD pour les invitations
   - `UserViewSet`: CRUD pour les utilisateurs
   - `InvitationAcceptView`: Vue pour accepter une invitation
   - `UserRoleView`: Vue pour gérer les rôles d'un utilisateur

4. **Service d'envoi d'email**:
   - Mise en place d'un service d'envoi d'email pour les invitations
   - Utilisation du template HTML existant

### Frontend (React/TypeScript)

1. **Fonctionnalités à ajouter à `UserManagement`**:
   - Amélioration du tableau des utilisateurs
   - Ajout d'une fonctionnalité de recherche/filtrage
   - Ajout d'une pagination

2. **Améliorations à `InviteUserModal`**:
   - Validation plus stricte des emails
   - Meilleure UX pour la sélection des rôles

3. **Ajout de confirmation pour actions critiques**:
   - Confirmation pour désactiver un utilisateur
   - Confirmation pour renvoyer une invitation

4. **Page d'acceptation d'invitation**:
   - Création d'une nouvelle page pour l'acceptation d'invitation
   - Formulaire de création de mot de passe

5. **Mise à jour des hooks**:
   - Amélioration de `useAdmin` pour gérer les nouvelles fonctionnalités
   - Ajout de fonctions pour la gestion des rôles

## Détails d'implémentation

### Backend (Django)

#### 1. Invitation et Création d'un Utilisateur

```python
# views.py
class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [IsAdministrator]
    
    def get_queryset(self):
        return Invitation.objects.all()
    
    def perform_create(self, serializer):
        # Générer un token et une date d'expiration (72h)
        # Enregistrer l'invitation
        invitation = serializer.save(invited_by=self.request.user)
        # Envoyer l'email d'invitation
        send_invitation_email(invitation)
        
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        invitation = self.get_object()
        # Mettre à jour la date d'expiration
        # Renvoyer l'email
        send_invitation_email(invitation, is_resend=True)
        return Response({"detail": "Invitation renvoyée avec succès"})
```

#### 2. Gestion de la Liste des Utilisateurs

```python
# views.py
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdministrator]
    
    def get_queryset(self):
        return User.objects.all()
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.status = 'active'
        user.save()
        return Response({"detail": "Utilisateur activé avec succès"})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.status = 'inactive'
        user.save()
        return Response({"detail": "Utilisateur désactivé avec succès"})
    
    @action(detail=True, methods=['post'])
    def update_roles(self, request, pk=None):
        user = self.get_object()
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Supprimer tous les rôles actuels
        UserRole.objects.filter(user=user).delete()
        
        # Ajouter les nouveaux rôles
        for role_id in serializer.validated_data['roles']:
            UserRole.objects.create(
                user=user,
                role_id=role_id
            )
        
        return Response({"detail": "Rôles mis à jour avec succès"})
```

#### 3. Acceptation d'invitation

```python
# views.py
class InvitationAcceptView(generics.GenericAPIView):
    serializer_class = InvitationAcceptSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            invitation = Invitation.objects.get(token=token, is_accepted=False)
            
            # Vérifier si l'invitation n'a pas expiré
            if invitation.expires_at < timezone.now():
                return Response(
                    {"detail": "Cette invitation a expiré."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response({
                "email": invitation.email,
                "first_name": invitation.first_name,
                "last_name": invitation.last_name,
                "company": invitation.company,
            })
            
        except Invitation.DoesNotExist:
            return Response(
                {"detail": "Invitation invalide ou déjà acceptée."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, token):
        try:
            invitation = Invitation.objects.get(token=token, is_accepted=False)
            
            # Vérifier si l'invitation n'a pas expiré
            if invitation.expires_at < timezone.now():
                return Response(
                    {"detail": "Cette invitation a expiré."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=invitation.email,
                email=invitation.email,
                first_name=invitation.first_name,
                last_name=invitation.last_name,
                company=invitation.company,
                password=serializer.validated_data['password'],
                status='active'
            )
            
            # Assigner les rôles
            for role in invitation.roles.all():
                UserRole.objects.create(user=user, role=role)
            
            # Marquer l'invitation comme acceptée
            invitation.is_accepted = True
            invitation.save()
            
            # Générer un token JWT pour l'utilisateur
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "detail": "Compte créé avec succès",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
            
        except Invitation.DoesNotExist:
            return Response(
                {"detail": "Invitation invalide ou déjà acceptée."},
                status=status.HTTP_404_NOT_FOUND
            )
```

### Frontend (React/TypeScript)

#### 1. Page d'administration des utilisateurs

```tsx
// UserManagement.tsx
function UserManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  
  // Pagination et filtrage
  const filteredUsers = users.filter(user => 
    user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );
  
  // Rendu du tableau
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Gestion des Utilisateurs</CardTitle>
          <Button onClick={() => setIsInviteModalOpen(true)}>
            <UserPlus className="mr-2 h-4 w-4" />
            Inviter un utilisateur
          </Button>
        </div>
        <div className="mt-2">
          <Input
            placeholder="Rechercher un utilisateur..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rôles</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedUsers.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  {user.first_name} {user.last_name}
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <RoleBadges roles={user.roles.map(ur => ur.role)} />
                </TableCell>
                <TableCell>
                  <UserStatusBadge status={user.status} />
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem onClick={() => handleOpenDetailModal(user)}>
                        Voir les détails
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => handleToggleStatus(user)}>
                        {user.status === 'active' ? 'Désactiver' : 'Activer'}
                      </DropdownMenuItem>
                      {user.status === 'pending' && (
                        <DropdownMenuItem onClick={() => handleResendInvitation(user)}>
                          Renvoyer l'invitation
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {/* Pagination */}
        <div className="flex justify-end mt-4">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                />
              </PaginationItem>
              {/* Pages numbers */}
              <PaginationItem>
                <PaginationNext
                  onClick={() => setCurrentPage(prev => 
                    Math.min(Math.ceil(filteredUsers.length / itemsPerPage), prev + 1)
                  )}
                  disabled={currentPage >= Math.ceil(filteredUsers.length / itemsPerPage)}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      </CardContent>
      
      {/* Modals */}
      <UserDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        user={selectedUser}
        onUserUpdated={fetchUsers}
      />
      
      <InviteUserModal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        onSubmit={handleCreateInvitation}
        roles={roles}
        isLoading={loading.invitations}
      />
    </Card>
  );
}
```

#### 2. Page d'acceptation d'invitation

```tsx
// AcceptInvitation.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/hooks/use-toast';
import { validateInvitation, acceptInvitation } from '@/lib/api/auth';

const passwordSchema = z
  .object({
    password: z.string()
      .min(8, "Le mot de passe doit contenir au moins 8 caractères")
      .regex(/[A-Z]/, "Le mot de passe doit contenir au moins une majuscule")
      .regex(/[a-z]/, "Le mot de passe doit contenir au moins une minuscule")
      .regex(/[0-9]/, "Le mot de passe doit contenir au moins un chiffre"),
    confirmPassword: z.string(),
  })
  .refine(data => data.password === data.confirmPassword, {
    message: "Les mots de passe ne correspondent pas",
    path: ["confirmPassword"],
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function AcceptInvitation() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [invitation, setInvitation] = useState<{
    email: string;
    first_name: string;
    last_name: string;
    company: string;
  } | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });
  
  // Valider le token d'invitation
  useEffect(() => {
    const validateToken = async () => {
      try {
        if (!token) {
          throw new Error('Token d\'invitation manquant');
        }
        
        const data = await validateInvitation(token);
        setInvitation(data);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Invitation invalide ou expirée');
        setLoading(false);
        
        toast({
          title: 'Erreur',
          description: err.message || 'Invitation invalide ou expirée',
          variant: 'destructive',
        });
      }
    };
    
    validateToken();
  }, [token, toast]);
  
  const onSubmit = async (values: PasswordFormValues) => {
    try {
      if (!token) {
        throw new Error('Token d\'invitation manquant');
      }
      
      const response = await acceptInvitation(token, values.password);
      
      // Stocker les tokens JWT
      localStorage.setItem('accessToken', response.access);
      localStorage.setItem('refreshToken', response.refresh);
      
      toast({
        title: 'Succès',
        description: 'Votre compte a été créé avec succès',
      });
      
      // Rediriger vers le dashboard
      navigate('/dashboard');
    } catch (err: any) {
      toast({
        title: 'Erreur',
        description: err.message || 'Erreur lors de la création du compte',
        variant: 'destructive',
      });
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-benaya-700"></div>
      </div>
    );
  }
  
  if (error || !invitation) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">Invitation invalide</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-red-500">{error}</p>
            <p className="text-center mt-4">
              L'invitation que vous essayez d'utiliser est invalide ou a expiré.
              Veuillez contacter l'administrateur pour obtenir une nouvelle invitation.
            </p>
          </CardContent>
          <CardFooter className="flex justify-center">
            <Button onClick={() => navigate('/auth')}>
              Retour à la page de connexion
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Créer votre compte</CardTitle>
          <CardDescription className="text-center">
            Vous avez été invité à rejoindre {invitation.company}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <div className="text-sm font-medium">Nom</div>
                <div>{invitation.first_name} {invitation.last_name}</div>
              </div>
              <div className="flex justify-between">
                <div className="text-sm font-medium">Email</div>
                <div>{invitation.email}</div>
              </div>
              <div className="flex justify-between">
                <div className="text-sm font-medium">Entreprise</div>
                <div>{invitation.company}</div>
              </div>
            </div>
            
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mot de passe</FormLabel>
                      <FormControl>
                        <Input type="password" placeholder="********" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Confirmer le mot de passe</FormLabel>
                      <FormControl>
                        <Input type="password" placeholder="********" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <Button type="submit" className="w-full mt-6">
                  Créer mon compte
                </Button>
              </form>
            </Form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

## Plan d'implémentation

### Étape 1: Backend

1. Développer les serializers pour les invitations et la gestion des utilisateurs
2. Implémenter les vues pour la gestion des invitations et des utilisateurs
3. Configurer les URLs pour accéder aux nouveaux endpoints
4. Ajouter le service d'envoi d'email pour les invitations
5. Tester les endpoints avec Postman ou des tests automatisés

### Étape 2: Frontend

1. Mettre à jour le client API pour consommer les nouveaux endpoints
2. Améliorer les composants existants (UserManagement, InviteUserModal)
3. Créer la page d'acceptation d'invitation
4. Mettre à jour les hooks (useAdmin, useAuth)
5. Configurer les routes pour la page d'acceptation d'invitation
6. Tester les fonctionnalités

### Étape 3: Intégration et Tests

1. Tester le flux complet d'invitation et d'acceptation
2. Tester la gestion des utilisateurs (activation/désactivation, modification des rôles)
3. Corriger les bugs et optimiser les performances
4. Déployer la nouvelle version 